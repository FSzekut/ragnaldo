"""Interface Streamlit do RAGnaldo com inicialização sob demanda."""

from __future__ import annotations

import sys
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

if question := st.chat_input("O que você quer descobrir?"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Consultando os vetores, porque reler tudo seria muito 2022..."):
            documents = runtime.search(question)
        if not documents:
            answer = "Não encontrei evidência no corpus. O jurídico vetorial mandou não inventar."
            st.markdown(answer)
        else:
            answer = (
                "Encontrei estes trechos relevantes. A geração da resposta fundamentada "
                "será conectada no próximo notebook do agente."
            )
            st.markdown(answer)
            for document in documents:
                ui.render_source(document)

    st.session_state.messages.append({"role": "assistant", "content": answer})
