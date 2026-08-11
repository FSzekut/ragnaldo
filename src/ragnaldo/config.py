"""Configuração central do RAGnaldo."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
# Conteúdo de terceiros já convertido para um formato textual (HTML e Notion,
# por exemplo). Fica fora do Git e é reconstruído pelo pipeline de fontes.
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
AUTHORIAL_SOURCES_DIR = PROJECT_ROOT / "docs" / "sources"
VECTOR_STORE_DIR = PROJECT_ROOT / "artifacts" / "vector_store"
EXECUTION_LOG_PATH = PROJECT_ROOT / "artifacts" / "logs" / "execution.jsonl"

# Precisa vir antes das dataclasses: os defaults abaixo são avaliados quando a
# classe é definida, então um .env carregado depois não teria efeito algum.
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class RagSettings:
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    # 4 era pouco: em perguntas curtas e coloquiais, o trecho que responde de
    # fato apareceu em oitavo lugar. Recuperar mais e cortar depois custa alguns
    # milissegundos de busca local; recuperar de menos custa a resposta.
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "10"))
    device: str = os.getenv("EMBEDDING_DEVICE", "cpu")


@dataclass(frozen=True)
class GenerationSettings:
    provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    model: str = os.getenv("LLM_MODEL", "claude-sonnet-5")
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    # None significa "não mandar o parâmetro". Os modelos mais recentes o
    # rejeitam; defina LLM_TEMPERATURE apenas se o modelo escolhido aceitar.
    temperature: float | None = (
        float(os.environ["LLM_TEMPERATURE"]) if os.getenv("LLM_TEMPERATURE") else None
    )

    # O FAISS com vetores normalizados devolve distância L2 ao quadrado: 0 é
    # idêntico, 2 é ortogonal, distância = 2 - 2 * similaridade de cosseno.
    #
    # O corte tem dois estágios porque a distância não é comparável entre
    # perguntas: uma pergunta longa no vocabulário do corpus produz 0.7, e uma
    # curta e coloquial sobre o mesmo assunto produz 1.15. Um limiar absoluto
    # único rejeitaria a segunda ou aceitaria qualquer coisa na primeira.
    #
    # 1) O MELHOR resultado precisa estar abaixo de best_max. É ele que
    #    distingue "o corpus tem algo sobre isso" de "não tem": medido, uma
    #    pergunta legítima teve melhor=1.156 e uma fora do corpus, 1.450.
    # 2) Os demais entram se estiverem dentro de relative_margin do melhor,
    #    o que se adapta à escala de cada pergunta em vez de fixá-la.
    best_max: float = float(os.getenv("RETRIEVAL_BEST_MAX", "1.35"))
    relative_margin: float = float(os.getenv("RETRIEVAL_RELATIVE_MARGIN", "0.25"))

    # Piso de trechos, aplicado depois da margem. Quando um chunk é muito melhor
    # que os demais, a margem descarta todo o resto e sobra ele sozinho — e como
    # o texto foi partido a cada mil caracteres, esse trecho único costuma ser
    # metade de uma seção. O modelo então responde que a informação "foi cortada
    # antes de detalhar", o que é verdade e não deveria acontecer: a continuação
    # estava no chunk seguinte, descartada por ser um pouco mais distante.
    min_evidence: int = int(os.getenv("RETRIEVAL_MIN_EVIDENCE", "4"))

    # Segunda tentativa, depois da reescrita: limiar mais exigente que o da
    # primeira. Medido em 10/08: reformular aproxima QUALQUER pergunta do
    # corpus, inclusive as que devem ser recusadas — "como declarar imposto
    # de renda" saiu de 1.547 para 1.360, a dez milésimos de ser aceita sob
    # o corte normal. A reescrita já teve a chance de otimizar a formulação;
    # se ainda assim ficou perto do limite, o corpus não tem a resposta.
    rewrite_best_max: float = float(os.getenv("RETRIEVAL_REWRITE_BEST_MAX", "1.25"))

    # Reescrever é tarefa curta e mecânica: não paga o modelo da resposta.
    rewrite_model: str = os.getenv("LLM_REWRITE_MODEL", "claude-haiku-4-5-20251001")

    # repr=False não é preciosismo: RagSettings é impresso no notebook 01, cujos
    # outputs são versionados. Uma chave dentro do repr acabaria num repositório
    # público sem que ninguém tivesse escrito a chave em lugar nenhum.
    # O strip() é defesa em profundidade. A chave viaja por .env, Secret Manager
    # e variável de ambiente, e qualquer um desses caminhos pode agregar um "\n"
    # invisível — um pipe de shell basta. A quebra de linha vai parar no header
    # x-api-key, que não a aceita, e a requisição morre antes de sair com um
    # erro de conexão que não menciona a causa em lugar nenhum.
    api_key: str = field(
        default_factory=lambda: os.getenv("LLM_API_KEY", "").strip(),
        repr=False,
        compare=False,
    )


SETTINGS = RagSettings()
GENERATION = GenerationSettings()
