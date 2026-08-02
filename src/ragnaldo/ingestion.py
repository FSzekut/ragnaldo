"""Pipeline offline de documentos, chunks, embeddings e índice FAISS."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ragnaldo.config import SETTINGS, VECTOR_STORE_DIR, RagSettings

MANIFEST_NAME = "artifact_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_sources(*directories: Path) -> list[Path]:
    supported = {".pdf", ".md", ".txt"}
    return sorted(
        path
        for directory in directories
        if directory.exists()
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in supported
    )


def load_sources(paths: Iterable[Path]) -> list[Document]:
    documents: list[Document] = []
    for path in paths:
        if path.suffix.lower() == ".pdf":
            loaded = PyPDFLoader(str(path)).load()
        else:
            loaded = TextLoader(str(path), encoding="utf-8").load()

        source_hash = sha256_file(path)
        for document in loaded:
            document.metadata.update(
                {
                    "source": path.name,
                    "source_path": str(path),
                    "source_sha256": source_hash,
                }
            )
        documents.extend(loaded)
    return documents


def split_documents(
    documents: list[Document], settings: RagSettings = SETTINGS
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)
    for position, chunk in enumerate(chunks):
        identity = "|".join(
            [
                chunk.metadata.get("source_sha256", ""),
                str(chunk.metadata.get("page", "")),
                str(chunk.metadata.get("start_index", "")),
                chunk.page_content,
            ]
        )
        chunk.metadata["chunk_id"] = hashlib.sha256(identity.encode()).hexdigest()[:16]
        chunk.metadata["chunk_position"] = position
    return chunks


def create_embeddings(settings: RagSettings = SETTINGS) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": settings.device},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 16},
    )


def build_index(
    chunks: list[Document],
    destination: Path = VECTOR_STORE_DIR,
    settings: RagSettings = SETTINGS,
) -> dict:
    if not chunks:
        raise ValueError("Nenhum chunk foi produzido; o índice não será criado.")

    destination.mkdir(parents=True, exist_ok=True)
    vector_store = FAISS.from_documents(chunks, create_embeddings(settings))
    vector_store.save_local(str(destination))

    artifact_hashes = {
        path.name: sha256_file(path)
        for path in destination.iterdir()
        if path.is_file() and path.name != MANIFEST_NAME
    }
    source_hashes = {
        chunk.metadata["source"]: chunk.metadata["source_sha256"] for chunk in chunks
    }
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "chunk_count": len(chunks),
        "source_hashes": source_hashes,
        "artifact_hashes": artifact_hashes,
    }
    (destination / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def verify_index(destination: Path = VECTOR_STORE_DIR) -> dict:
    manifest_path = destination / MANIFEST_NAME
    if not manifest_path.exists():
        raise FileNotFoundError(
            "Índice ainda não criado. Execute o notebook 01_ingestao_e_embeddings."
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for filename, expected_hash in manifest["artifact_hashes"].items():
        artifact = destination / filename
        if not artifact.is_file() or sha256_file(artifact) != expected_hash:
            raise RuntimeError(f"Artefato ausente ou alterado: {filename}")
    return manifest


def load_verified_index(
    destination: Path = VECTOR_STORE_DIR,
    settings: RagSettings = SETTINGS,
) -> tuple[FAISS, dict]:
    manifest = verify_index(destination)
    if manifest["embedding_model"] != settings.embedding_model:
        raise RuntimeError(
            "O modelo configurado difere daquele usado para construir o índice."
        )

    # FAISS.save_local usa pickle para o docstore. A desserialização só ocorre
    # depois que todos os artefatos são verificados contra o manifesto local.
    vector_store = FAISS.load_local(
        str(destination),
        create_embeddings(settings),
        allow_dangerous_deserialization=True,
    )
    return vector_store, manifest
