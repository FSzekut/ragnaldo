# Diretrizes do projeto RAGnaldo

## Identidade

**Nome:** RAGnaldo  
**Conceito:** guia inteligente, útil e bem-humorado sobre o ONE AI for Tech, a jornada Tech Builder e o próprio projeto que o implementa.  
**Frase provisória:** "Responde com fontes. Quando não sabe, admite — habilidade ainda rara entre humanos e chatbots."

O humor faz parte da experiência, mas nunca deve substituir a precisão. Toda afirmação factual deve permanecer ancorada nas fontes recuperadas.

## Objetivo do Challenge

Construir um agente funcional que responda a perguntas baseadas em documentos, com:

- repositório público no GitHub;
- histórico de commits coerente;
- estrutura organizada;
- README completo;
- leitura e processamento de PDF ou CSV;
- agente inteligente funcional;
- deploy público na nuvem;
- link e captura de tela como evidência.

Embora o enunciado original mencione OCI, foi confirmado que o deploy na GCP é permitido. O projeto será publicado no Google Cloud Run aproveitando os créditos disponíveis.

## Problema e público

O RAGnaldo não será um chatbot genérico de RH, vendas ou atendimento. Ele deverá entregar valor para:

- participantes e interessados no ONE AI for Tech;
- pessoas estudando agentes, RAG e LangChain;
- avaliadores que desejem compreender a solução;
- recrutadores ou profissionais técnicos que visitem o portfólio.

O agente deverá responder sobre:

- programa ONE e jornada Tech Builder;
- agentes de IA, RAG, LangChain, LangGraph, automação e cloud;
- requisitos do Challenge;
- arquitetura e decisões do próprio RAGnaldo;
- testes, limitações, custos e aprendizados do projeto.

## Corpus inicial planejado

O corpus será estático e composto preferencialmente por:

1. relatório oficial **Oracle AI Insights — América Latina 2025**;
2. conteúdo público oficial sobre o ONE AI for Tech, preservando URL e data de consulta;
3. enunciado do Challenge Alura Agente;
4. um dossiê autoral do RAGnaldo, descrevendo arquitetura, decisões, testes e aprendizados.

Toda fonte deverá possuir procedência clara. Conteúdo de terceiros não deverá ser apresentado como autoral nem republicado de forma indevida.

## Arquitetura decidida

```text
Pipeline de ingestão (offline)
PDFs -> extração -> chunks -> embeddings locais -> índice persistido

Aplicação (Cloud Run)
landing leve -> inicialização sob demanda -> modelo local + índice pronto
-> retriever -> agente -> resposta fundamentada com fontes
```

### Ingestão

- LangChain como camada de orquestração do RAG;
- `PyPDFLoader` para PDFs textuais;
- `RecursiveCharacterTextSplitter` como primeira estratégia de chunking;
- modelo multilíngue local de embeddings;
- índice vetorial persistido e versionado;
- metadados mínimos: fonte, página, identificador do chunk e versão/hash do documento;
- reconstrução do índice somente quando o corpus ou a configuração de ingestão mudar.

### Serving

- os embeddings dos documentos serão pré-calculados;
- o modelo local continuará em produção para gerar o embedding de cada pergunta;
- recursos pesados serão carregados apenas quando o usuário inicializar o agente;
- `st.cache_resource` deverá impedir recargas desnecessárias na mesma instância;
- a interface mostrará progresso/animação durante a primeira carga;
- respostas deverão apresentar fontes e páginas quando disponíveis;
- sem evidência suficiente, o agente deverá declarar que não encontrou a resposta.

### Aplicação e infraestrutura

- interface em Streamlit;
- notebooks como ambiente principal de aprendizado e experimentação, seguindo o padrão da Alura;
- código reutilizável será gradualmente extraído para `src/ragnaldo` quando estabilizado;
- Docker para empacotamento;
- Cloud Run para deploy;
- GitHub Actions para testes e entrega contínua;
- segredos fora do repositório;
- aplicação pública e simples de avaliar, sem autenticação privada obrigatória.

## Reaproveitamento consciente

### Do `second_brain_24_7`

- experiência com Streamlit e UX;
- Docker, Cloud Run e GitHub Actions;
- lazy loading;
- segurança e gerenciamento de segredos;
- conhecimento adquirido ao implementar RAG diretamente com NumPy.

### De `~/projects/tech_builder`

- `PyPDFLoader`;
- `RecursiveCharacterTextSplitter`;
- `HuggingFaceEmbeddings`;
- vector stores e retrievers do LangChain;
- cadeias LCEL;
- ferramentas e LangGraph;
- avaliação do RAG, HyDE e recuperação avançada como possíveis evoluções.

O RAGnaldo não será uma simples cópia. A implementação deverá demonstrar entendimento e registrar as razões de cada escolha.

## Decisões ainda abertas

- modelo definitivo de embeddings após benchmark em português;
- FAISS versus outro vector store local persistente;
- provedor do modelo gerador;
- conjunto final de documentos;
- estratégia de avaliação e limiar de relevância;
- identidade visual definitiva;
- necessidade de ferramenta adicional além da recuperação documental.

## Princípios de desenvolvimento

1. Começar simples e medir antes de adicionar complexidade.
2. Separar ingestão de serving.
3. Não regenerar embeddings de documentos estáticos no startup.
4. Preservar fontes e rastreabilidade em todo o pipeline.
5. Preferir componentes substituíveis e configuração por ambiente.
6. Nunca commitar tokens, credenciais, documentos privados ou artefatos sensíveis.
7. Cada commit deve representar uma etapa compreensível do desenvolvimento.
8. Notebooks devem ser executáveis em ordem, com explicações e resultados reproduzíveis.
9. O README final deve incluir arquitetura, execução, exemplos reais e evidência do deploy.
10. Humor na apresentação; rigor na recuperação.

## Regra de segurança antes de commits

Nenhum commit deverá ser criado sem uma verificação imediatamente anterior do conteúdo que será versionado. A checagem mínima inclui:

1. revisar `git diff --cached` e a lista completa de arquivos staged;
2. procurar tokens, chaves, senhas, credenciais e dados pessoais;
3. confirmar que `.env`, caches, modelos, documentos privados e artefatos pesados continuam ignorados;
4. executar `pip check`, testes e análise estática disponíveis;
5. revisar dependências e arquivos baixados de terceiros;
6. só então criar o commit, registrando no relatório da sessão o resultado da verificação.

Em caso de dúvida, o commit deve ser adiado.

## Humor e mensagens provisórias

- "Consultando os vetores — porque reler 29 páginas seria muito 2022."
- "Modelo acordando. Até a inteligência artificial precisa de alguns segundos."
- "Não encontrei isso nas fontes. Poderia inventar, mas o jurídico vetorial não deixou."
- "Carregando embeddings locais: economia também é uma feature."
- "RAGnaldo encontrou evidências. Milagre não; similaridade de cosseno."

Essas mensagens são provisórias e deverão ser usadas com moderação.
