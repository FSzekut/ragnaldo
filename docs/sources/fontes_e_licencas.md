# Fontes, procedência e uso

Data da pesquisa: **1º de agosto de 2026**.

## Política do corpus

O RAGnaldo separa conteúdo oficial de conteúdo autoral. Documentos de terceiros são baixados de suas páginas originais por `scripts/download_sources.py`, permanecem ignorados pelo Git e não são apresentados como propriedade do projeto.

O arquivo `data/sources.json` registra URLs, hashes observados e o status temporal de cada fonte. Uma página web mutável pode mudar após a data da captura; documentos marcados como históricos não devem fundamentar regras atuais do programa.

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

## Fonte indisponível

O link para o manual atual dos candidatos, indicado pela página oficial, retornou HTTP 404 durante a pesquisa:

<https://grupoalura.notion.site/imersao-agentes-ia-one>

O link foi preservado para tentativa manual posterior.

## Conteúdo autoral

Os documentos `guia_one_ai_for_tech.md`, `challenge_alura_agente.md` e `dossie_ragnaldo.md` foram redigidos para este projeto. Eles distinguem fatos confirmados, decisões do projeto e pontos ainda em aberto.
