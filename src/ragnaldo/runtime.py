"""Recursos carregados sob demanda pela aplicação Streamlit."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from ragnaldo.config import SETTINGS
from ragnaldo.generation import ExecutionRecord, answer_question
from ragnaldo.ingestion import load_verified_index


@dataclass
class RagRuntime:
    vector_store: object
    manifest: dict

    def search(self, question: str) -> list[Document]:
        return self.vector_store.similarity_search(question, k=SETTINGS.retrieval_k)

    def answer(self, question: str) -> tuple[str, list[Document], ExecutionRecord]:
        return answer_question(question, self.vector_store)


def load_runtime() -> RagRuntime:
    vector_store, manifest = load_verified_index()
    return RagRuntime(vector_store=vector_store, manifest=manifest)
