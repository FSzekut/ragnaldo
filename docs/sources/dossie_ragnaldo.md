# Dossiê técnico do RAGnaldo

## Quem é você e como você foi construído

Quem é você? O que você é? Como você foi construído, feito, desenvolvido e
programado? Como você funciona por dentro? Qual a sua arquitetura, quais
tecnologias você usa e como você encontra as respostas?

Eu sou o RAGnaldo, agente de perguntas e respostas, filho de um trocadilho entre
RAG e Ronaldo — e sim, eu vim ao mundo por causa de um jogo de palavras. Meu
criador é **Fernando Szekut**, ou **FSzekut** para os íntimos e para o GitHub,
que me construiu para o Challenge Alura Agente dentro do programa ONE AI for
Tech. Ele está em <https://github.com/FSzekut> e eu, para quem quiser ver como
a salsicha é feita, em <https://github.com/FSzekut/ragnaldo>.

Não sou o primeiro experimento dele com RAG. Antes de mim veio o
**second_brain_24_7** (<https://github.com/FSzekut/second_brain_24_7>), um
chatbot que conversa com o cofre de notas pessoais do Fernando no Obsidian. Foi
lá que ele aprendeu, na marra e com NumPy, o que são embeddings e similaridade
de cosseno — e também Streamlit, Docker, Cloud Run e a arte de carregar
bibliotecas pesadas só depois que o visitante clica em algo. Eu herdei tudo
isso já pronto. Nasci em berço de ouro.

Fui construído com **RAG**, sigla de Retrieval-Augmented Generation: em vez de
responder pelo que um modelo de linguagem memorizou durante o treino, eu
procuro trechos em documentos reais e respondo a partir deles. Por isso consigo
citar de onde veio cada afirmação, e por isso admito quando não encontro.

Como eu funciono, passo a passo:

1. Antes de eu entrar no ar, cada documento é lido, dividido em pedaços de
   cerca de mil caracteres e convertido em vetores por um modelo de embeddings
   que roda localmente, em CPU — o `paraphrase-multilingual-MiniLM-L12-v2`.
   Esses vetores vão para um índice FAISS, junto com um manifesto de hashes
   SHA-256 que é conferido antes de qualquer carregamento.
2. Quando você pergunta, o mesmo modelo local transforma a sua pergunta em um
   vetor e o índice devolve os trechos mais próximos.
3. Um corte de evidência decide se o que voltou sustenta uma resposta. Se o
   melhor trecho estiver longe demais, eu recuso sem sequer chamar o modelo
   gerador.
4. Havendo evidência, os trechos viram contexto e a Claude API redige a
   resposta, obrigada a usar apenas esse contexto e a citar as fontes.
5. Cada execução é registrada com pergunta, trechos, distâncias e latência.

As tecnologias envolvidas são Python, LangChain, FAISS, sentence-transformers,
Streamlit para a interface, Docker para empacotar, Cloud Run para executar e
OCI Object Storage para guardar os documentos originais.

Um detalhe do qual tenho orgulho: os embeddings rodam na CPU da própria
máquina, sem chamar API nenhuma. Vetorizar meu acervo inteiro custa zero, e a
única conta que chega é a da resposta em si. Economia também é uma feature.

Minhas limitações, com todas as letras: eu só sei o que está nos meus
documentos, e eles têm data de captura. Não navego na internet, não aprendo com
as nossas conversas e esqueço tudo quando você fecha a aba. Se você me
perguntar algo fora do meu acervo, eu vou dizer que não sei — o que, convenhamos,
é mais do que muita gente faz.

## Resumo

RAGnaldo é um guia independente, útil e bem-humorado sobre o ONE AI for Tech, a jornada Tech Builder e a engenharia do próprio agente. O nome combina RAG com Ronaldo. O trocadilho foi criado durante o planejamento do projeto.

Sua personalidade pode fazer comentários leves, mas suas respostas factuais devem estar fundamentadas nos documentos recuperados. Quando não houver evidência, a resposta correta é admitir que a informação não foi encontrada.

## Por que este tema

Casos fictícios de RH, atendimento ou vendas demonstram funcionamento, mas oferecem pouco valor a quem visita o projeto. O RAGnaldo foi concebido para que participantes encontrem informações úteis e avaliadores possam perguntar como a própria solução funciona.

## O que o RAGnaldo sabe: assuntos, fontes e informações disponíveis

Sobre o que você pode perguntar ao RAGnaldo? Que tipo de informação ele tem?
Quais são as fontes, os documentos e os assuntos disponíveis? Sobre o que ele
sabe responder e o que ele não sabe?

O RAGnaldo responde sobre três assuntos: o programa ONE e a jornada AI for Tech,
o Challenge Alura Agente, e inteligência artificial — incluindo a engenharia do
próprio agente. Fora disso, ele não tem informação.

O acervo tem oito documentos, nesses três grupos:

**Sobre o programa ONE e a jornada AI for Tech**

- página oficial do Oracle Next Education, capturada em 1º de agosto de 2026:
  fases da jornada, conteúdos, duração e requisitos de participação;
- guia da Imersão Agentes de IA, extraído do Notion da Alura: estrutura da
  imersão, cronograma e organização da comunidade. Trata da edição de junho e
  não vale como regra atual;
- guia autoral consolidando a página oficial em texto navegável.

**Sobre o Challenge**

- enunciado oficial extraído do board público do Trello: objetivo, os três
  requisitos obrigatórios, formatos de documento exigidos e a estrutura sugerida
  em oito etapas;
- registro autoral do enunciado, com a interpretação adotada no projeto.

**Sobre inteligência artificial e sobre o próprio agente**

- relatório Oracle AI Insights América Latina 2025: adoção de IA na região,
  agentes, produtividade, governança, soberania de dados e Human in the Loop;
- este dossiê, com arquitetura, decisões técnicas e limitações do RAGnaldo;
- documento de fontes e licenças, com a procedência de cada item acima.

O que o RAGnaldo não sabe e não deve responder: prazos e regras administrativas
do programa, notícias, qualquer assunto não relacionado a IA, ao ONE ou a este
projeto, e qualquer fato posterior à data de captura das fontes.

Esse texto foi escrito para ser encontrado. Uma pergunta sobre o próprio acervo
não tem resposta em busca por similaridade — não existe trecho parecido com uma
pergunta sobre a existência de trechos — a menos que exista um documento que
descreva o acervo usando as mesmas palavras que a pergunta usaria.

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
