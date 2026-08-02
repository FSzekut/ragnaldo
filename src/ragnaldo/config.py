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
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "4"))
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
    # idêntico, 2 é ortogonal, e distância = 2 - 2 * similaridade de cosseno.
    # 1.2 equivale a cosseno 0.4 e barra apenas o que está claramente fora do
    # assunto. É um chute honesto: a calibração real depende dos dados e é
    # tarefa do notebook 04, que tem a distância de cada consulta registrada.
    max_distance: float = float(os.getenv("RETRIEVAL_MAX_DISTANCE", "1.2"))

    # repr=False não é preciosismo: RagSettings é impresso no notebook 01, cujos
    # outputs são versionados. Uma chave dentro do repr acabaria num repositório
    # público sem que ninguém tivesse escrito a chave em lugar nenhum.
    api_key: str = field(
        default_factory=lambda: os.getenv("LLM_API_KEY", ""),
        repr=False,
        compare=False,
    )


SETTINGS = RagSettings()
GENERATION = GenerationSettings()
