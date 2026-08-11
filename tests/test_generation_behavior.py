
"""Comportamento observável de answer_question, travado antes da migração.

Estes testes descrevem o que o código faz hoje, não o que ele deveria fazer.
São rede de segurança para a troca da chain por um grafo: se a migração
preservar o comportamento, eles continuam verdes sem nenhuma alteração.
"""

from __future__ import annotations

import json

import pytest
from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from ragnaldo import generation
from ragnaldo.generation import REFUSAL, answer_question


class FakeVectorStore:
    """Devolve resultados fixos, para que o corte seja o único sob teste."""

    def __init__(self, results):
        self._results = results

    def similarity_search_with_score(self, question, k):
        return self._results


def _document(chunk_id: str = "c1") -> Document:
    return Document(
        page_content="O ONE AI for Tech é uma jornada de formação.",
        metadata={"source": "landing", "location": "seção 1", "chunk_id": chunk_id},
    )


def test_sem_evidencia_recusa_sem_chamar_o_modelo(tmp_path, monkeypatch):
    # Distância alta o bastante para reprovar em qualquer limiar plausível.
    store = FakeVectorStore([(_document(), 2.0)])

    def nao_deveria_ser_chamado(*_args, **_kwargs):
        raise AssertionError("build_model foi chamado numa pergunta sem evidência")

    monkeypatch.setattr(generation, "build_model", nao_deveria_ser_chamado)

    answer, documents, record = answer_question(
        "qual a receita de bolo de cenoura?",
        store,
        log_path=tmp_path / "execution.jsonl",
    )

    assert answer == REFUSAL
    assert documents == []
    assert record.refused is True
    assert record.retrieved == []


def test_com_evidencia_responde_e_registra_a_procedencia(tmp_path, monkeypatch):
    store = FakeVectorStore([(_document("c7"), 0.5)])
    monkeypatch.setattr(
        generation,
        "build_model",
        lambda *_a, **_k: FakeListChatModel(responses=["É uma jornada de formação."]),
    )
    log_path = tmp_path / "execution.jsonl"

    answer, documents, record = answer_question(
        "o que é o ONE AI for Tech?", store, log_path=log_path
    )

    assert answer == "É uma jornada de formação."
    assert len(documents) == 1
    assert record.refused is False
    assert record.error is None
    assert record.retrieved[0].chunk_id == "c7"
    assert record.retrieved[0].distance == 0.5

    # O registro precisa chegar ao disco, não só ao objeto devolvido.
    linha = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert linha["question"] == "o que é o ONE AI for Tech?"
    assert linha["refused"] is False


def test_falha_do_modelo_e_registrada_antes_de_propagar(tmp_path, monkeypatch):
    store = FakeVectorStore([(_document(), 0.5)])

    def explode(_):
        raise RuntimeError("provedor fora do ar")

    monkeypatch.setattr(
        generation, "build_model", lambda *_a, **_k: RunnableLambda(explode)
    )
    log_path = tmp_path / "execution.jsonl"

    with pytest.raises(RuntimeError):
        answer_question("o que é o ONE?", store, log_path=log_path)

    # O comportamento que importa: a execução com erro fica registrada.
    linha = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert linha["error"].startswith("RuntimeError")
    assert linha["answer"] == ""