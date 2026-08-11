"""O fluxo de decisão do RAGnaldo como grafo de estados.

A chain LCEL anterior expressava bem o caminho feliz e escondia a decisão
que mais importa: recusar antes de chamar a API. Aqui ela é uma aresta
condicional, visível no desenho.

Cronômetro e registro ficam fora, em answer_question: são instrumentação,
não domínio.
"""

from __future__ import annotations

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


def build_graph(vector_store, settings: GenerationSettings = GENERATION):
    def recuperar_evidencia(state: RagState) -> RagState:
        results = vector_store.similarity_search_with_score(
            state["question"], k=SETTINGS.retrieval_k
        )
        evidence = generation.select_evidence(results, settings)

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

    def tem_evidencia(state: RagState) -> str:
        return "gerar" if state["evidence"] else "recusar"

    def recusar(state: RagState) -> RagState:
        # Sem chamada de API: sem evidência ela só produziria uma
        # alucinação educada, e ainda cobraria por ela.
        return {"answer": generation.REFUSAL, "error": None}

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
    graph.add_node("recusar", recusar)
    graph.add_node("gerar", gerar)

    graph.add_edge(START, "recuperar_evidencia")
    graph.add_conditional_edges(
        "recuperar_evidencia", tem_evidencia, {"gerar": "gerar", "recusar": "recusar"}
    )
    graph.add_edge("recusar", END)
    graph.add_edge("gerar", END)

    return graph.compile()