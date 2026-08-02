# Challenge Alura Agente — enunciado oficial

Fonte: board público do Trello do Challenge AluraAgente — ONE IA FOR TECH (pt-BR),
consultado em 2 de agosto de 2026. Em caso de divergência, o enunciado exibido
dentro da plataforma Alura é a referência final.

## Objetivo

Desenvolver um agente de inteligência artificial corporativo, acessível a todos os
colaboradores, capaz de responder perguntas com base em documentos internos de uma
empresa. O agente deve compreender e processar múltiplos formatos de arquivo e
cobrir diferentes domínios organizacionais, funcionando como uma base de
conhecimento conversacional, centralizada e sempre disponível.

Formatos citados no enunciado: **PDF, Word, Excel, PowerPoint, Markdown, CSV, JSON
e HTML**.

## Requisitos obrigatórios

O enunciado lista exatamente três:

1. Colocar o projeto num repositório público no GitHub.
2. Realizar o deploy do agente na nuvem Oracle (OCI). **Deve-se utilizar ao menos
   um serviço OCI no challenge.**
3. Inserir no README uma imagem ou vídeo do agente sendo executado em nuvem.

O card 7 reforça o requisito 2: "nenhuma tecnologia ou serviço mencionado é
obrigatório de usar. Porém, é obrigatório usar ao menos 1 serviço do ecossistema
OCI neste processo de deploy".

Entre os serviços OCI sugeridos no card 7 estão OCIR, Compute, Container
Instances, OKE, **Object Storage para os arquivos originais**, Autonomous Database,
Vault para segredos e OCI DevOps para CI/CD.

## Registro de execução

O card 8 pede que a execução seja documentada: pergunta recebida, contexto
recuperado, resposta gerada, timestamp e latência. É necessário executar em nuvem
e adicionar mídia (foto ou vídeo) como registro dessa execução no README.

## Liberdade de escopo

O card "Ponto de atenção" é explícito: "Todos os passos aqui são apenas sugestões
da estrutura do projeto. Em outras palavras, você pode fazer o seu projeto como
desejar, desde que realize as funcionalidades mencionadas". A lista de temas
sugeridos (e-commerce, SaaS, logística, saúde, educação, fintech) também é
apresentada como referência, não como obrigação.

É essa cláusula que sustenta a escolha de tema do RAGnaldo, descrita em
`dossie_ragnaldo.md`: em vez de uma empresa fictícia, o corpus trata do programa
ONE AI for Tech e da engenharia do próprio agente.

## Estrutura sugerida (cards de backlog)

Os oito cards de backlog descrevem um pipeline de referência: coleta e organização
de documentos, processamento e extração de conteúdo, indexação vetorial, camada de
recuperação, geração e validação de respostas, implantação e interface, deploy na
OCI e registro de execução. São sugestões, não requisitos.

## Correção de registro

Uma versão anterior deste documento afirmava que "foi confirmado que o uso de outra
nuvem é permitido". Isso estava errado: o enunciado oficial exige ao menos um
serviço OCI. O registro foi corrigido após a leitura do board.
