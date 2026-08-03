# RAGnaldo

> Um guia inteligente e bem-humorado sobre o ONE AI for Tech, o Tech Builder e a própria engenharia por trás deste agente.

O RAGnaldo é o projeto desenvolvido para o Challenge Alura Agente. A aplicação usará RAG para responder a perguntas com base em documentos públicos e em documentação autoral do projeto, sempre apresentando as fontes recuperadas.

## Status

🚧 Projeto em construção. Ingestão multiformato, índice vetorial verificado, recuperação com corte de evidência e geração fundamentada estão funcionando de ponta a ponta. Faltam o deploy e o registro da execução em nuvem. As decisões estão registradas em [`diretrizes.md`](diretrizes.md).

## Arquitetura

```text
Ingestão (offline, sem custo de API)
PDF DOCX XLSX PPTX MD TXT CSV JSON HTML
    -> tabela LOADERS -> chunks -> embeddings locais -> FAISS + manifesto de hashes

Serving
pergunta -> embedding local -> busca vetorial -> corte de evidência
                                                      |
                                       nada sobrou? -> recusa (sem chamar a API)
                                       sobrou?      -> contexto com procedência
                                                      -> Claude -> resposta + fontes
                                                      -> registro de execução
```

Os embeddings são locais em todas as etapas, inclusive para a pergunta. A API do modelo gerador é chamada **uma vez por pergunta**, e apenas quando existe evidência que sustente uma resposta.

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

## Configuração do modelo gerador

```bash
cp .env.example .env
```

Preencha com o provedor, o modelo e a chave. O `.env` é ignorado pelo Git:

```
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-5
LLM_API_KEY=sk-ant-...
```

Opcionais: `LLM_MAX_TOKENS` (padrão 1024), `RETRIEVAL_MAX_DISTANCE` (padrão 1.2) e `LLM_TEMPERATURE`, que só deve ser definida se o modelo escolhido aceitar o parâmetro — os mais recentes o rejeitam.

## Exemplos

### Pergunta dentro do corpus

> **O que o ONE AI for Tech ensina sobre RAG e LangChain?**
>
> O ONE AI for Tech aborda esses temas na frente "Engenharia de IA e RAG com LangChain". Segundo o contexto, os pontos ensinados são LangChain e orquestração de LLMs, RAG para buscar informação em documentos reduzindo alucinações, e RAG avançado com chunking, embeddings, bancos vetoriais, reescrita de perguntas e avaliação de qualidade. (…)
>
> `(Fonte: one_ai_for_tech_oracle_snapshot.html)`

A resposta citou duas fontes. Outros trechos entraram no contexto mas não sustentavam nenhuma afirmação, e o modelo os descartou em vez de costurá-los ao texto. Latência de 6,9 s.

### Pergunta fora do corpus

> **Qual foi o placar da final da Copa do Mundo de 1970?**
>
> Não encontrei isso nas fontes que eu tenho. Poderia inventar, mas o jurídico vetorial não deixou.

A busca devolveu dez resultados, como sempre devolve — o melhor a 1,450, longe demais para sustentar qualquer coisa. Nenhum virou contexto, e a recusa saiu em **19 ms sem chamar a API**.

## Corte de evidência

A busca sempre retorna `k` resultados: para uma pergunta sobre algo ausente do corpus, ela devolve os menos ruins, não os bons. O que decide se existe resposta é o corte, em dois estágios:

1. **o melhor resultado precisa estar abaixo de `best_max` (1,35)** — é ele que separa "o corpus trata desse assunto" de "não trata";
2. **os demais entram se ficarem dentro de `relative_margin` (0,25) do melhor** — o que se adapta à escala de cada pergunta;
3. **pelo menos `min_evidence` (4) trechos são enviados** quando os dois primeiros estágios deixam menos.

O terceiro estágio corrige um efeito colateral do segundo: quando um trecho é muito melhor que os demais, a margem descarta todo o resto e sobra ele sozinho — e como o texto é dividido a cada mil caracteres, esse trecho isolado costuma ser metade de uma seção. O modelo então responde, com razão, que a informação "foi cortada antes de detalhar", enquanto a continuação estava no chunk seguinte.

O segundo estágio existe porque a distância não é comparável entre perguntas. "O que o ONE ensina sobre RAG e LangChain?" produz 0,71; "para quem é o programa ONE?", sobre o mesmo corpus, produz 1,16. Um limiar absoluto único rejeitaria a segunda ou aceitaria qualquer coisa na primeira — foi exatamente o que aconteceu na primeira calibração deste projeto, feita com uma única pergunta de exemplo.

O corte decide se **há assunto**, não se há resposta. Perguntas com vocabulário sobreposto ao corpus passam de propósito, e quem recusa ali é o modelo, que recebe o contexto e vê que ele trata de outra coisa.

## Avaliação

```bash
python scripts/eval_retrieval.py
```

Dezesseis perguntas com expectativa declarada: onze que o corpus responde — várias em linguagem coloquial, que é onde a recuperação falhava — e cinco que ele não responde. O script falha se a calibração regredir.

Isso não é teste unitário e não pode ser: nos dois modos de falha de um RAG (silêncio indevido e resposta indevida) o código está correto. O que está errado é a calibração, e ela só aparece executando perguntas contra o índice real.

## Registro de execução

Cada pergunta gera uma linha em `artifacts/logs/execution.jsonl` com timestamp, pergunta, resposta, trechos recuperados com suas distâncias, latência, modelo e eventual erro. O arquivo fica fora do Git porque contém as perguntas reais de quem usa o agente.

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

Execute primeiro `01_ingestao_e_embeddings.ipynb` para gerar o índice. Depois `02_retrieval_e_rag.ipynb`, que percorre a recuperação, o corte de evidência, o prompt e a cadeia completa — terminando no teste que mais importa: uma pergunta que o corpus não responde.

## Interface

```bash
streamlit run app/main.py
```

A landing page é carregada sem importar torch, sentence-transformers, LangChain ou FAISS. Esses recursos entram em memória apenas quando o usuário inicializa o agente. Durante a primeira carga, a interface exibe uma animação com suporte a `prefers-reduced-motion`.

Abaixo de cada resposta ficam os trechos consultados, com fonte e localização. Eles são rotulados como consultados, não como citados: todos foram ao contexto do modelo, mas a resposta pode ter descartado os que não sustentavam nenhuma afirmação.

## Deploy

Cada push na `main` dispara `.github/workflows/deploy.yml`, que executa:

```text
testes e lint
    -> baixa os documentos do OCI Object Storage
    -> gera o índice vetorial
    -> avalia a recuperação   <- barra o deploy se a calibração regredir
    -> constrói a imagem e envia ao Artifact Registry
    -> publica no Cloud Run
```

O índice é construído no pipeline, não empacotado no repositório: os documentos-fonte são de terceiros e ficam fora do Git, e quem os guarda é o **OCI Object Storage**. É esse passo que atende ao requisito de usar ao menos um serviço OCI — e ele não é decorativo, porque sem o bucket o pipeline não teria as fontes para indexar.

A autenticação no GCP usa **Workload Identity Federation**: o GitHub emite um token de curta duração a cada execução e o Google o troca por credenciais temporárias. Nenhuma chave de conta de serviço existe como segredo. A chave da API do modelo fica no Secret Manager e é lida pelo Cloud Run em tempo de execução, nunca entrando na imagem.

A preparação da infraestrutura está em [`infrastructure/SETUP.md`](infrastructure/SETUP.md).

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

O commit só deve ser criado depois que essas verificações passarem. O `security_check.py` também está instalado como hook de `pre-commit`, e o repositório tem push protection ativo no GitHub.

A evidência do deploy será adicionada quando a aplicação estiver publicada.
