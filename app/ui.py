"""Componentes visuais leves do RAGnaldo."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).parent / "assets"


def configure_page() -> None:
    st.set_page_config(
        page_title="RAGnaldo",
        page_icon="🧭",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@500;600;700&display=swap">',
        unsafe_allow_html=True,
    )
    css = (ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_brand(compact: bool = False) -> None:
    compact_class = " brand-compact" if compact else ""
    st.markdown(
        f"""
        <section class="brand{compact_class}">
          <div class="brand-mark" aria-hidden="true">
            <span class="brand-node node-a"></span>
            <span class="brand-node node-b"></span>
            <span class="brand-node node-c"></span>
            <span class="brand-core">R</span>
          </div>
          <div>
            <p class="eyebrow">// guia não-oficial do Tech Builder</p>
            <h1>RAGNALDO</h1>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_landing() -> bool:
    render_brand()
    st.markdown(
        """
        <p class="hero-copy">
          Pergunte sobre ONE AI for Tech, agentes, RAG e a engenharia deste projeto.
          As respostas usam documentos rastreáveis. Quando a fonte não sabe,
          o RAGnaldo também não finge que sabe.
        </p>
        <div class="feature-grid">
          <div><span>01</span><strong>fontes visíveis</strong></div>
          <div><span>02</span><strong>embeddings locais</strong></div>
          <div><span>03</span><strong>humor controlado</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.button(
        "Inicializar o RAGnaldo",
        type="primary",
        use_container_width=True,
        key="initialize_ragnaldo",
    )


def loading_markup(stage: str) -> str:
    return f"""
    <div class="loading-shell" role="status" aria-live="polite">
      <div class="vector-loader" aria-hidden="true">
        <span class="orbit orbit-a"><i></i></span>
        <span class="orbit orbit-b"><i></i></span>
        <span class="loader-core">R</span>
      </div>
      <p class="loading-label">{stage}</p>
      <p class="loading-joke">Modelo acordando. Até a inteligência artificial precisa de alguns segundos.</p>
    </div>
    """


# Quatro perguntas que a suíte de scripts/eval_retrieval.py cobre. Sugerir algo
# que o corpus não responde bem seria convidar o visitante à única experiência
# ruim disponível logo na primeira interação.
SUGGESTED_QUESTIONS = [
    "Quem é você?",
    "Para quem é o programa ONE?",
    "Quais os requisitos do Challenge?",
    "Como você foi construído?",
]


def render_suggestions() -> str | None:
    """Mostra perguntas prontas e devolve a escolhida, se houver.

    Uma caixa de texto vazia é o pior primeiro contato com um agente de corpus
    fechado: quem chega não sabe o que ele sabe, chuta algo fora do acervo e
    recebe uma recusa — correta, e ainda assim a pior porta de entrada possível.
    """
    st.caption("Não sabe por onde começar?")
    columns = st.columns(2)
    for position, question in enumerate(SUGGESTED_QUESTIONS):
        if columns[position % 2].button(
            question, key=f"suggestion_{position}", use_container_width=True
        ):
            return question
    return None


def render_source(document, prefix: str = "") -> None:
    # location já chega formatado pela ingestão ("página 3", "slide 5",
    # "planilha Vendas"); "documento" é o genérico e não acrescenta nada.
    location = document.metadata.get("location")
    label = f" · {location}" if location and location != "documento" else ""
    source = document.metadata.get("source", "fonte desconhecida")
    with st.expander(f"{prefix}{source}{label}"):
        st.write(document.page_content)


def render_evidence(documents, answer: str) -> None:
    """Separa o que sustentou a resposta do que apenas foi consultado.

    Dez trechos idênticos em aparência transferem ao leitor o trabalho de
    descobrir quais importaram — e num projeto que promete rastreabilidade, é
    justamente esse o trabalho que a interface deveria fazer. A separação usa a
    citação que o modelo já escreveu no texto.
    """
    citados, consultados = [], []
    for document in documents:
        source = document.metadata.get("source", "")
        (citados if source and source in answer else consultados).append(document)

    if citados:
        st.caption(f"Fontes citadas na resposta ({len(citados)}):")
        for document in citados:
            render_source(document, prefix="✓ ")

    if consultados:
        rotulo = "Também consultados, sem sustentar afirmações"
        st.caption(f"{rotulo} ({len(consultados)}):")
        for document in consultados:
            render_source(document)
