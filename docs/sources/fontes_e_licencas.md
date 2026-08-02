# Fontes, procedência e uso

Data da pesquisa inicial: **1º de agosto de 2026**. Última revisão: **2 de agosto de 2026**.

## Política do corpus

O RAGnaldo separa conteúdo oficial de conteúdo autoral. Documentos de terceiros são baixados de suas páginas originais por `scripts/download_sources.py`, permanecem ignorados pelo Git e não são apresentados como propriedade do projeto.

O arquivo `data/sources.json` registra URLs, hashes observados e o status temporal de cada fonte. Uma página web mutável pode mudar após a data da captura; documentos marcados como históricos não devem fundamentar regras atuais do programa.

O manifesto tem duas listas. Em `sources` ficam as fontes que `download_sources.py` obtém com uma requisição HTTP simples e verificação de hash. Em `derived_sources` ficam aquelas cuja obtenção exige um caminho próprio — API pública, conversão de formato — e que por isso não são reproduzidas pelo script. As duas listas alimentam o índice; a distinção é sobre como o arquivo chega ao disco, não sobre confiabilidade.

## Fontes oficiais

### Oracle AI Insights — América Latina 2025

- Publicador: Oracle.
- URL: <https://www.oracle.com/br/a/ocom/docs/a-nova-era-da-ia.pdf>
- Uso no agente: conceitos de IA, agentes, adoção na América Latina, produtividade, governança, soberania de dados, Human in the Loop e infraestrutura.

### ONE — Oracle Next Education

- Publicador: Oracle.
- URL: <https://www.oracle.com/br/education/oracle-next-education/>
- Uso no agente: estrutura atual da jornada ONE AI for Tech, conteúdos, duração, fases e objetivos.
- Observação: por ser uma página mutável, informações temporais devem citar a data da captura.

### Manual histórico do ONE

- Publicadores: Oracle e Alura.
- URL: <https://www.oracle.com/br/a/ocom/docs/pt-ebook-manual-do-aluno-oracle-next.pdf>
- Uso no agente: apenas contexto histórico.
- Restrição: não usar para responder prazos, fases ou regras da edição atual.

## Fontes derivadas

Estas fontes exigiram um método próprio de obtenção e estão registradas em
`derived_sources`, fora do alcance de `download_sources.py`.

### Board do Challenge AluraAgente

- Publicador: Alura.
- URL: <https://trello.com/b/IhB0NmMm/challenge-aluraagente-one-ia-for-tech-pt-br>
- Obtenção: o Trello expõe boards públicos como JSON em `/b/<id>.json`. Os 20 cards foram exportados e convertidos em Markdown.
- Uso no agente: enunciado oficial, requisitos obrigatórios, formatos exigidos e estrutura sugerida do projeto.
- Observação: é a referência que corrigiu a premissa equivocada sobre a nuvem do deploy.

### Imersão Agentes de IA — ONE

- Publicador: Alura.
- URL: <https://grupoalura.notion.site/imersao-agentes-ia-one>
- Obtenção: a página é servida como aplicação JavaScript, e um cliente sem execução de scripts recebe HTML vazio. O conteúdo foi obtido pela API pública `/api/v3/loadPageChunk`, percorrendo a árvore de blocos.
- Uso no agente: apenas contexto do programa.
- Restrição: é o guia da imersão de junho, **não** o enunciado do Challenge. Não deve fundamentar regras ou prazos da etapa atual.
- Correção de registro: uma versão anterior deste documento marcava esta URL como HTTP 404. O erro veio do cliente automatizado, não do servidor — a página responde HTTP 200.

## Conteúdo autoral

Os documentos `guia_one_ai_for_tech.md`, `challenge_alura_agente.md` e `dossie_ragnaldo.md` foram redigidos para este projeto. Eles distinguem fatos confirmados, decisões do projeto e pontos ainda em aberto.
