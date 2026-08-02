# Dossiê técnico do RAGnaldo

## Resumo

RAGnaldo é um guia independente, útil e bem-humorado sobre o ONE AI for Tech, a jornada Tech Builder e a engenharia do próprio agente. O nome combina RAG com Ronaldo. O trocadilho foi criado durante o planejamento do projeto.

Sua personalidade pode fazer comentários leves, mas suas respostas factuais devem estar fundamentadas nos documentos recuperados. Quando não houver evidência, a resposta correta é admitir que a informação não foi encontrada.

## Por que este tema

Casos fictícios de RH, atendimento ou vendas demonstram funcionamento, mas oferecem pouco valor a quem visita o projeto. O RAGnaldo foi concebido para que participantes encontrem informações úteis e avaliadores possam perguntar como a própria solução funciona.

## Arquitetura

O sistema separa ingestão e serving.

Na ingestão, documentos são carregados, divididos em chunks e transformados em vetores por um modelo local de embeddings acessado pela interface do LangChain. O índice e seus metadados são persistidos antes do deploy.

No serving, a aplicação carrega o modelo local e o índice já produzido. Cada pergunta ainda precisa ser transformada em embedding, mas os documentos estáticos não são reprocessados durante o startup.

## Embeddings locais

Embeddings locais foram escolhidos para evitar custo por requisição e porque o corpus é estático. O primeiro candidato é `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, por ser multilíngue, relativamente pequeno e adequado a execução em CPU.

O modelo definitivo deverá ser confirmado por benchmark em português. A decisão não deve ser baseada apenas em popularidade.

## Cold start e lazy loading

O Cloud Run pode iniciar uma nova instância depois de um período sem uso. Carregar bibliotecas de machine learning, o modelo de embeddings e o índice aumenta o tempo da primeira interação.

Para melhorar a experiência, a aplicação entrega primeiro uma landing page leve. Os imports pesados e os recursos do RAG são carregados somente quando o visitante escolhe inicializar o agente. Durante esse período, uma animação e mensagens de progresso explicam o que está acontecendo. O recurso carregado é mantido em cache dentro da instância.

Esse padrão reaproveita um aprendizado do projeto `second_brain_24_7`, no qual a tela de acesso era exibida antes dos SDKs e componentes pesados.

## Reaproveitamento e autoria

O projeto reutiliza conhecimento, não apenas código. O `second_brain_24_7` ensinou Streamlit, Docker, Cloud Run, CI/CD, UX, segurança, RAG e lazy loading. Os notebooks em `tech_builder` oferecem exemplos de `PyPDFLoader`, text splitters, embeddings, vector stores, retrievers, LCEL e LangGraph.

No RAGnaldo, esses elementos serão reorganizados para um corpus novo, uma interface própria, avaliação explícita e uma arquitetura documentada para o Challenge.

## Segurança dos artefatos

Fontes de terceiros são obtidas por URLs registradas em manifesto. Arquivos estáticos recebem hashes SHA-256. O índice vetorial deve ser carregado apenas quando seus artefatos corresponderem ao manifesto gerado pelo pipeline confiável.

Nenhum segredo deve entrar no Git. Antes de cada commit devem ser revisados os arquivos staged, padrões de credenciais, dependências e testes.

## Experiência pretendida

Exemplos de mensagens da interface:

- “Consultando os vetores, porque reler 29 páginas seria muito 2022.”
- “Modelo acordando. Até a inteligência artificial precisa de alguns segundos.”
- “Não encontrei isso nas fontes. Poderia inventar, mas o jurídico vetorial não deixou.”
- “Carregando embeddings locais: economia também é uma feature.”

O humor deve ser curto e nunca alterar citações ou respostas técnicas.

## Decisões em aberto

- modelo gerador e provedor;
- modelo definitivo de embeddings;
- parâmetros de chunking e recuperação;
- limiar para recusa;
- estratégia final de avaliação;
- identidade visual definitiva;
- configuração de CPU, memória e concorrência no Cloud Run.
