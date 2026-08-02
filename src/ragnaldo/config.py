"""Configuração central do RAGnaldo."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
# Conteúdo de terceiros já convertido para um formato textual (HTML e Notion,
# por exemplo). Fica fora do Git e é reconstruído pelo pipeline de fontes.
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
AUTHORIAL_SOURCES_DIR = PROJECT_ROOT / "docs" / "sources"
VECTOR_STORE_DIR = PROJECT_ROOT / "artifacts" / "vector_store"


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


SETTINGS = RagSettings()
