# RAGnaldo

> Um guia inteligente e bem-humorado sobre o ONE AI for Tech, o Tech Builder e a própria engenharia por trás deste agente.

O RAGnaldo é o projeto desenvolvido para o Challenge Alura Agente. A aplicação usará RAG para responder a perguntas com base em documentos públicos e em documentação autoral do projeto, sempre apresentando as fontes recuperadas.

## Status

🚧 Projeto em construção. A pesquisa das fontes, o pipeline inicial de ingestão e a landing page com lazy loading já estão estruturados. As decisões estão registradas em [`diretrizes.md`](diretrizes.md).

## Arquitetura planejada

```text
Documentos -> ingestão offline -> embeddings locais -> índice persistido
                                                        |
Usuário -> Streamlit -> agente/retriever ----------------+
                     -> resposta com fontes
```

## Estrutura

```text
ragnaldo/
├── notebooks/       # aprendizado, experimentos e evolução do RAG
├── src/ragnaldo/     # componentes reutilizáveis estabilizados
├── app/              # aplicação Streamlit
├── data/raw/         # documentos-fonte não sensíveis
├── data/processed/   # conteúdo intermediário reproduzível
├── artifacts/        # índice vetorial e metadados gerados
├── tests/            # testes automatizados
├── docs/             # documentação e evidências
├── infrastructure/   # Docker, Cloud Run e CI/CD
└── assets/           # imagens e recursos visuais
```

## Preparação local

```bash
python3 -m venv env
source env/bin/activate
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -m ipykernel install --sys-prefix --name ragnaldo --display-name "Python (RAGnaldo)"
```

## Fontes

Baixe as fontes públicas registradas no manifesto:

```bash
python scripts/download_sources.py
```

Arquivos de terceiros permanecem fora do Git. URLs, hashes e status temporal estão em [`data/sources.json`](data/sources.json). A documentação de procedência está em [`docs/sources/fontes_e_licencas.md`](docs/sources/fontes_e_licencas.md).

## Notebooks

```bash
jupyter lab
```

Execute primeiro `01_ingestao_e_embeddings.ipynb` para gerar o índice. Depois use `02_retrieval_e_rag.ipynb` para inspecionar a recuperação e o prompt fundamentado.

## Interface

```bash
streamlit run app/main.py
```

A landing page é carregada sem importar torch, sentence-transformers, LangChain ou FAISS. Esses recursos entram em memória apenas quando o usuário inicializa o agente. Durante a primeira carga, a interface exibe uma animação com suporte a `prefers-reduced-motion`.

## Segurança antes de commits

Depois de revisar e adicionar os arquivos desejados ao staging:

```bash
python scripts/security_check.py
python -m pip check
python -m pip_audit
pytest
ruff check .
git diff --cached
```

O commit só deve ser criado depois que essas verificações passarem.

As perguntas de exemplo, respostas geradas e evidências do deploy serão adicionadas após a escolha do modelo gerador e a validação do agente completo.
