# RAGnaldo

> Um guia inteligente e bem-humorado sobre o ONE AI for Tech, o Tech Builder e a própria engenharia por trás deste agente.

O RAGnaldo é o projeto desenvolvido para o Challenge Alura Agente. A aplicação usará RAG para responder a perguntas com base em documentos públicos e em documentação autoral do projeto, sempre apresentando as fontes recuperadas.

## Status

🚧 Projeto em construção. As decisões iniciais estão registradas em [`diretrizes.md`](diretrizes.md).

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

As instruções completas de execução, tecnologias, perguntas de exemplo e evidências do deploy serão adicionadas conforme as etapas forem implementadas e validadas.

