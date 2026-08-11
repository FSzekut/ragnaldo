"""O fluxo de decisão do RAGnaldo como grafo de estados.

A chain LCEL anterior expressava bem o caminho feliz e escondia a decisão
que mais importa: recusar antes de chamar a API. Aqui ela é uma aresta
condicional, visível no desenho.

Cronômetro e registro ficam fora, em answer_question: são instrumentação,
não domínio.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TypedDict

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, START, StateGraph

from ragnaldo import generation
from ragnaldo.config import GENERATION, SETTINGS, GenerationSettings


class RagState(TypedDict, total=False):
    """O que trafega entre os nós.

    Fora daqui de propósito: documents, results, retrieved e refused, todos
    deriváveis de evidence em uma linha.
    """

    question: str
    evidence: list[tuple[Document, float]]
    descartados: list[float]      # distâncias, já convertidas de np.float32
    answer: str
    error: str | None
    reescrita: str | None      # None enquanto não houve tentativa


def build_graph(vector_store, settings: GenerationSettings = GENERATION):
    def recuperar_evidencia(state: RagState) -> RagState:
        # Na segunda passada vale a pergunta reescrita e um limiar mais
        # exigente: a reescrita já teve a chance de otimizar a formulação.
        pergunta = state.get("reescrita") or state["question"]
        corte = settings
        if state.get("reescrita") is not None:
            corte = replace(settings, best_max=settings.rewrite_best_max)

        results = vector_store.similarity_search_with_score(
            pergunta, k=SETTINGS.retrieval_k
        )
        evidence = generation.select_evidence(results, corte)

        # select_evidence filtra a lista sem criar objetos novos, então
        # identidade basta para saber o que ficou de fora. float() é
        # obrigatório: o FAISS devolve np.float32, que json.dumps recusa.
        aceitos = {id(documento) for documento, _ in evidence}
        return {
            "evidence": evidence,
            "descartados": [
                float(score)
                for documento, score in results
                if id(documento) not in aceitos
            ],
        }

    def rotear(state: RagState) -> str:
        if state["evidence"]:
            return "gerar"
        if state.get("reescrita") is None:
            return "reescrever"
        return "recusar"             # já tentou reescrever e não adiantou    # primeira falha: vale uma segunda chance

    def recusar(state: RagState) -> RagState:
        # Sem chamada de API: sem evidência ela só produziria uma
        # alucinação educada, e ainda cobraria por ela.
        return {"answer": generation.REFUSAL, "error": None}

    def reescrever(state: RagState) -> RagState:
        return {"reescrita": generation.rewrite_question(state["question"], settings)}

    def houve_mudanca(state: RagState) -> str:
        # Medido em 10/08: para pergunta fora de escopo o modelo devolve o
        # texto idêntico. Repetir a busca daria exatamente o mesmo resultado.
        if state["reescrita"] == state["question"]:
          return "recusar"
        return "recuperar_evidencia"

    def gerar(state: RagState) -> RagState:
        documents = [document for document, _ in state["evidence"]]
        chain = (
            generation.PROMPT
            | generation.build_model(settings)
            | StrOutputParser()
        )
        try:
            answer = chain.invoke(
                {
                    "context": generation.format_context(documents),
                    "question": state["question"],
                }
            )
            return {"answer": answer, "error": None}
        except Exception as exception:  # noqa: BLE001
            return {
                "answer": "",
                "error": f"{type(exception).__name__}: {exception}",
            }

    graph = StateGraph(RagState)
    graph.add_node("recuperar_evidencia", recuperar_evidencia)
    graph.add_node("reescrever", reescrever)
    graph.add_node("recusar", recusar)
    graph.add_node("gerar", gerar)

    graph.add_edge(START, "recuperar_evidencia")
    graph.add_conditional_edges(
        "recuperar_evidencia",
        rotear,
        {"gerar": "gerar", "reescrever": "reescrever", "recusar": "recusar"},
    )
    graph.add_conditional_edges(
        "reescrever",
        houve_mudanca,
        {"recuperar_evidencia": "recuperar_evidencia", "recusar": "recusar"},
    )
    graph.add_edge("recusar", END)
    graph.add_edge("gerar", END)

    return graph.compile()