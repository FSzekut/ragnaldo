"""Geração fundamentada: contexto recuperado, resposta com fontes e registro.

A recuperação já entrega trechos com procedência. Aqui eles viram uma resposta,
sob duas regras: o modelo não pode afirmar nada fora do contexto, e toda execução
fica registrada (pergunta, evidência, resposta, latência), como pede o card 8 do
enunciado.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ragnaldo.config import EXECUTION_LOG_PATH, GENERATION, GenerationSettings

REFUSAL = (
    "Não encontrei isso nas fontes que eu tenho. Poderia inventar, "
    "mas o jurídico vetorial não deixou."
)

SYSTEM_PROMPT = """Você é o RAGnaldo, um guia independente e bem-humorado sobre o \
ONE AI for Tech, a jornada Tech Builder e a engenharia do próprio agente.

Regras, em ordem de prioridade:

1. Responda fatos usando exclusivamente o CONTEXTO abaixo. Seu conhecimento prévio
   não vale como fonte, mesmo que você tenha certeza.
2. Se o contexto não sustentar a resposta, diga que não encontrou a informação.
   Uma recusa correta vale mais que uma resposta plausível. Não preencha lacunas.
3. Não invente datas, regras, prazos, números, páginas ou nomes de fonte.
4. Ao citar, use exatamente o rótulo de fonte que aparece no contexto.
5. Se o contexto responder apenas parte da pergunta, responda essa parte e diga
   explicitamente o que ficou de fora.
6. Humor: no máximo uma frase curta, nunca dentro de uma citação e nunca quando a
   resposta for uma recusa por falta de evidência.

Responda em português do Brasil, em prosa direta.

CONTEXTO:
{context}"""

PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{question}")]
)


@dataclass
class RetrievedChunk:
    """O que foi recuperado, achatado para caber numa linha de log."""

    source: str
    location: str
    chunk_id: str
    distance: float


@dataclass
class ExecutionRecord:
    timestamp: str
    question: str
    answer: str
    refused: bool
    model: str
    latency_ms: int
    retrieved: list[RetrievedChunk] = field(default_factory=list)
    error: str | None = None


def format_context(documents: list[Document]) -> str:
    """Monta o contexto com a procedência que o modelo deve copiar ao citar.

    O rótulo vem pronto dos metadados. O modelo nunca precisa deduzir uma
    referência, que é justamente onde uma LLM inventaria com mais naturalidade.
    """
    blocks = []
    for document in documents:
        source = document.metadata.get("source", "fonte desconhecida")
        location = document.metadata.get("location", "documento")
        chunk = document.metadata.get("chunk_id", "?")
        blocks.append(
            f"[Fonte: {source} | trecho: {location} | id: {chunk}]\n"
            f"{document.page_content}"
        )
    return "\n\n---\n\n".join(blocks)


def select_evidence(
    results: list[tuple[Document, float]],
    settings: GenerationSettings = GENERATION,
) -> list[tuple[Document, float]]:
    """Decide se há evidência e, havendo, quanto dela vale enviar ao modelo.

    A busca sempre devolve k resultados, mesmo para uma pergunta sobre algo que
    não existe no corpus: ela retorna os menos ruins, não os bons. O corte é o
    que impede esses trechos de chegarem ao modelo como contexto legítimo.

    São dois estágios, porque a distância não é comparável entre perguntas —
    a mesma dúvida rende 0.7 escrita no vocabulário do corpus e 1.15 escrita
    de forma coloquial:

    1. o melhor resultado responde "o corpus sabe algo sobre isso?";
    2. a margem relativa responde "quais dos demais acompanham o melhor?",
       adaptando-se à escala daquela pergunta específica.
    """
    if not results:
        return []

    best = min(score for _, score in results)
    if best > settings.best_max:
        return []

    limit = best + settings.relative_margin
    ordered = sorted(results, key=lambda item: item[1])
    selected = [item for item in ordered if item[1] <= limit]

    # Um trecho isolado costuma ser meia seção, porque o divisor corta por
    # tamanho e não por assunto. O piso recupera a vizinhança que a margem
    # descartou por pouco — e o modelo continua livre para ignorá-la.
    if len(selected) < settings.min_evidence:
        selected = ordered[: settings.min_evidence]

    return selected


def build_model(settings: GenerationSettings = GENERATION):
    # Import tardio, como o resto do serving: a landing page não deve carregar
    # o cliente HTTP do provedor antes de o visitante iniciar o agente.
    from langchain_anthropic import ChatAnthropic

    if settings.provider != "anthropic":
        raise RuntimeError(
            f"Provedor '{settings.provider}' não implementado. "
            "Ajuste LLM_PROVIDER no .env ou adicione o adaptador correspondente."
        )
    if not settings.api_key:
        raise RuntimeError(
            "LLM_API_KEY ausente. Copie .env.example para .env e preencha a chave."
        )

    # temperature só entra quando explicitamente configurada: os modelos mais
    # recentes rejeitam o parâmetro com HTTP 400, e mandá-lo "por via das dúvidas"
    # quebraria a cadeia inteira por causa de um default que ninguém pediu.
    optional = {}
    if settings.temperature is not None:
        optional["temperature"] = settings.temperature

    return ChatAnthropic(
        model=settings.model,
        api_key=settings.api_key,
        max_tokens=settings.max_tokens,
        timeout=60,
        stop=None,
        **optional,
    )


REWRITE_SYSTEM = """Você reformula perguntas para melhorar a busca semântica \
num acervo sobre o ONE AI for Tech (programa de formação da Oracle com a Alura), \
a jornada Tech Builder e a engenharia do agente RAGnaldo.

Reescreva a pergunta preservando exatamente a intenção original.

Regras:
1. Se a pergunta for sobre esses assuntos, prefira os termos que a documentação
   oficial usaria: "gratuito" no lugar de "pagar", "benefícios" no lugar de
   "vale a pena", "requisitos" no lugar de "o que preciso".
2. Se a pergunta for sobre o agente RAGnaldo, prefira os termos que a documentação
   oficial usaria: "RAGnaldo" no lugar de "agent", "engenharia" no lugar de
   "desenvolvimento", "ONE AI for Tech" no lugar de "programa de formação",
   "Jornada Tech Builder" no lugar de "jornada de formação".
3. Se a pergunta for sobre a jornada Tech Builder, prefira os termos que a documentação
   oficial usaria: "Jornada Tech Builder" no lugar de "jornada de formação",
   "ONE AI for Tech" no lugar de "programa de formação", "engenharia" no lugar de
   "desenvolvimento", "RAGnaldo" no lugar de "agent".
4. Não invente detalhes que o usuário não mencionou.
5. Devolva apenas a pergunta reescrita, sem aspas e sem explicação."""

REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [("system", REWRITE_SYSTEM), ("human", "{question}")]
)


def rewrite_question(question: str, settings: GenerationSettings = GENERATION) -> str:
    """Reescreve a pergunta para melhorar a busca semântica."""
    model = build_model(replace(settings, model=settings.rewrite_model))
    chain = REWRITE_PROMPT | model | StrOutputParser()
    return chain.invoke({"question": question}).strip()


def append_record(record: ExecutionRecord, log_path: Path = EXECUTION_LOG_PATH) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def answer_question(
    question: str,
    vector_store,
    settings: GenerationSettings = GENERATION,
    log_path: Path | None = EXECUTION_LOG_PATH,
) -> tuple[str, list[Document], ExecutionRecord]:
    """Responde à pergunta e devolve resposta, evidência usada e o registro.

    A latência medida cobre recuperação e geração juntas, que é o que o usuário
    espera de fato.
    """
    # Import tardio: graph.py importa este módulo, então o import no topo
    # fecharia um ciclo. Mesmo padrão que build_model já usa com ChatAnthropic.
    from ragnaldo.graph import build_graph

    started = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    final = build_graph(vector_store, settings).invoke({"question": question})

    evidence = final.get("evidence", [])
    documents = [document for document, _ in evidence]
    retrieved = [
        RetrievedChunk(
            source=document.metadata.get("source", "desconhecida"),
            location=document.metadata.get("location", "documento"),
            chunk_id=document.metadata.get("chunk_id", "?"),
            distance=round(float(score), 4),
        )
        for document, score in evidence
    ]
    answer = final.get("answer", "")
    error = final.get("error")

    record = ExecutionRecord(
        timestamp=timestamp,
        question=question,
        answer=answer,
        refused=not documents,
        model=settings.model,
        latency_ms=int((time.perf_counter() - started) * 1000),
        retrieved=retrieved,
        error=error,
    )
    if log_path is not None:
        append_record(record, log_path)

    if error is not None:
        raise RuntimeError(error)

    return answer, documents, record
