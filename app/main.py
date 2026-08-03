"""Interface Streamlit do RAGnaldo com inicialização sob demanda."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import ui

ui.configure_page()


@st.cache_resource(show_spinner=False)
def get_runtime():
    # Import tardio: torch, sentence-transformers, LangChain e FAISS não são
    # carregados enquanto o visitante está apenas na landing page.
    from ragnaldo.runtime import load_runtime

    return load_runtime()


def initialize() -> None:
    loading = st.empty()
    loading.markdown(ui.loading_markup("Carregando embeddings locais"), unsafe_allow_html=True)
    # A fronteira da UI precisa transformar falhas de modelo, rede ou artefato
    # em uma mensagem recuperável, sem derrubar toda a sessão do Streamlit.
    try:
        runtime = get_runtime()
    except Exception as error:  # noqa: BLE001
        loading.empty()
        st.session_state.runtime_error = str(error)
        return

    loading.markdown(ui.loading_markup("Conectando o índice vetorial"), unsafe_allow_html=True)
    st.session_state.runtime = runtime
    st.session_state.runtime_ready = True
    loading.empty()
    st.rerun()


if not st.session_state.get("runtime_ready", False):
    if ui.render_landing():
        initialize()

    if error := st.session_state.pop("runtime_error", None):
        st.warning(error)
        st.caption(
            "O front-end está pronto. Gere o índice executando o notebook "
            "01_ingestao_e_embeddings.ipynb."
        )
    st.stop()


ui.render_brand(compact=True)
runtime = st.session_state.runtime
st.caption(
    f"{runtime.manifest['chunk_count']} chunks · "
    f"{runtime.manifest['embedding_model']}"
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "RAGnaldo na área. Pergunte algo e eu procuro evidências antes de abrir a boca.",
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("O que você quer descobrir?") or st.session_state.pop(
    "pending_question", None
)

# As sugestões só existem enquanto não há nada a responder. Sem o "not question",
# o rerun disparado pelo clique redesenharia os botões antes de a resposta entrar
# no histórico — eles ficariam na tela carregando o estado da rodada anterior.
if (
    not question
    and len(st.session_state.messages) == 1
    and (escolhida := ui.render_suggestions())
):
    st.session_state.pending_question = escolhida
    st.rerun()

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Consultando os vetores, porque reler tudo seria muito 2022..."):
            try:
                answer, documents, record = runtime.answer(question)
            except Exception as error:  # noqa: BLE001
                # Falha do provedor não pode derrubar a sessão: a conversa
                # anterior continua legível e o usuário pode tentar de novo.
                # O traceback vai para stderr porque a mensagem na tela é curta
                # demais para diagnosticar — em produção, ela era tudo o que
                # existia, e os logs do Cloud Run não registravam nada.
                traceback.print_exc(file=sys.stderr)
                answer, documents, record = f"O modelo não respondeu: {error}", [], None
        st.markdown(answer)
        if documents:
            # Todos foram ao contexto do modelo, mas só alguns sustentaram o que
            # ele escreveu. Apresentar os dez como "fontes da resposta" seria uma
            # citação falsa dentro de um projeto que promete rastreabilidade.
            ui.render_evidence(documents, answer)
        if record is not None:
            st.caption(f"{record.latency_ms} ms")

    st.session_state.messages.append({"role": "assistant", "content": answer})
