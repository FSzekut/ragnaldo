
"""Comportamento observável de answer_question.

Escritos antes da migração da chain para o grafo, como rede de segurança:
descrevem o que o código faz, não o que deveria fazer. A migração passou sem
alterar nenhum deles.

O primeiro teste mudou depois, quando o ciclo de reescrita entrou. Não foi
regressão: sem evidência, o modelo da resposta continua nunca sendo chamado,
mas passou a existir uma chamada ao modelo barato, a da reescrita.
"""

from __future__ import annotations

import json

import pytest
from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from ragnaldo import generation
from ragnaldo.config import GENERATION
from ragnaldo.generation import REFUSAL, answer_question


class FakeVectorStore:
    """Devolve resultados fixos, e conta quantas buscas aconteceram.

    O contador é o que distingue uma volta pelo ciclo de reescrita de um
    atalho direto para a recusa.
    """

    def __init__(self, results):
        self._results = results
        self.chamadas = 0

    def similarity_search_with_score(self, question, k):
        self.chamadas += 1
        return self._results


def _document(chunk_id: str = "c1") -> Document:
    return Document(
        page_content="O ONE AI for Tech é uma jornada de formação.",
        metadata={"source": "landing", "location": "seção 1", "chunk_id": chunk_id},
    )


def test_sem_evidencia_recusa_chamando_apenas_a_reescrita(tmp_path, monkeypatch):
    """Sem evidência, o modelo da resposta nunca é chamado.

    O que existe é exatamente uma chamada ao modelo barato, a da reescrita.
    Travar isso impede que uma regressão futura traga a chamada cara de volta
    em silêncio, que é o tipo de erro que só aparece na fatura.
    """
    # Distância alta o bastante para reprovar em qualquer limiar plausível.
    store = FakeVectorStore([(_document(), 2.0)])
    modelos_pedidos = []

    def registra_e_reescreve(settings, *_args, **_kwargs):
        modelos_pedidos.append(settings.model)
        return FakeListChatModel(responses=["existe algum custo para participar?"])

    monkeypatch.setattr(generation, "build_model", registra_e_reescreve)

    answer, documents, record = answer_question(
        "qual a receita de bolo de cenoura?",
        store,
        log_path=tmp_path / "execution.jsonl",
    )

    assert answer == REFUSAL
    assert documents == []
    assert record.refused is True
    assert record.retrieved == []
    assert modelos_pedidos == [GENERATION.rewrite_model]
    # Duas buscas provam que a aresta de retorno foi percorrida de fato.
    assert store.chamadas == 2


def test_reescrita_identica_nao_repete_a_busca(tmp_path, monkeypatch):
    """Medido em 10/08: para pergunta fora de escopo o modelo devolve o texto
    intacto, nas quatro testadas. Repetir a busca daria exatamente o mesmo
    resultado, então o grafo corta caminho direto para a recusa.
    """
    pergunta = "qual a receita de bolo de cenoura?"
    store = FakeVectorStore([(_document(), 2.0)])

    monkeypatch.setattr(
        generation,
        "build_model",
        lambda *_a, **_k: FakeListChatModel(responses=[pergunta]),
    )

    answer, _documents, record = answer_question(
        pergunta, store, log_path=tmp_path / "execution.jsonl"
    )

    assert answer == REFUSAL
    assert record.refused is True
    assert store.chamadas == 1


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