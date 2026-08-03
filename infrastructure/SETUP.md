# Preparação da infraestrutura

Passos executados uma única vez, antes do primeiro deploy automático. Depois
disso, cada push na `main` publica sozinho.

Os valores usados aqui:

```bash
export PROJECT=meu-claude-ui-2026
export REGION=southamerica-east1
export REPO=ragnaldo
export SERVICE=ragnaldo
export GITHUB_REPO=FSzekut/ragnaldo
gcloud config set project "$PROJECT"
```

## 1. Habilitar as APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  iamcredentials.googleapis.com
```

## 2. Repositório de imagens

```bash
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Imagens do RAGnaldo"
```

## 3. Chave da API no Secret Manager

A chave **não** entra na imagem nem em variável de ambiente do workflow. O
Cloud Run a lê do Secret Manager em tempo de execução.

```bash
# Lê do .env local sem exibir a chave no terminal nem no histórico do shell.
# O "tr -d '\n'" não é opcional: grep e cut preservam a quebra de linha, ela
# entra no segredo e depois vai para o header x-api-key. Header HTTP não aceita
# newline, então o cliente aborta a requisição e devolve APIConnectionError —
# que parece problema de rede e não tem nada a ver com rede.
grep '^LLM_API_KEY=' .env | cut -d= -f2- | tr -d '\n' \
  | gcloud secrets create ragnaldo-llm-api-key --data-file=-
```

Para rotacionar depois:

```bash
grep '^LLM_API_KEY=' .env | cut -d= -f2- | tr -d '\n' \
  | gcloud secrets versions add ragnaldo-llm-api-key --data-file=-
```

Conferir se o segredo tem exatamente o tamanho esperado, sem exibir o valor:

```bash
gcloud secrets versions access latest --secret=ragnaldo-llm-api-key | wc -c
grep '^LLM_API_KEY=' .env | cut -d= -f2- | tr -d '\n' | wc -c
```

Os dois números precisam ser idênticos.

A conta de serviço que executa o Cloud Run precisa conseguir ler o segredo:

```bash
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding ragnaldo-llm-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role=roles/secretmanager.secretAccessor
```

## 4. Conta de serviço do deploy

```bash
gcloud iam service-accounts create github-deployer \
  --display-name="Deploy do RAGnaldo pelo GitHub Actions"

SA="github-deployer@${PROJECT}.iam.gserviceaccount.com"

for ROLE in roles/run.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:${SA}" --role="$ROLE" --condition=None
done
```

O `iam.serviceAccountUser` é o menos óbvio dos três: sem ele o deploy falha ao
tentar rodar o serviço como a conta de runtime do Cloud Run.

## 5. Workload Identity Federation

Isso substitui a chave JSON da conta de serviço. O GitHub emite um token de
curta duração a cada execução, e o GCP o troca por credenciais temporárias —
não existe credencial de longa duração guardada em lugar nenhum.

```bash
gcloud iam workload-identity-pools create github \
  --location=global --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc github \
  --location=global \
  --workload-identity-pool=github \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GITHUB_REPO}'"
```

A `attribute-condition` é obrigatória e não é burocracia: sem ela, **qualquer
repositório do GitHub, de qualquer pessoa**, poderia obter credenciais deste
projeto. Ela restringe a troca de token a este repositório específico.

```bash
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
POOL="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github"

gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL}/attribute.repository/${GITHUB_REPO}"

echo "GCP_WIF_PROVIDER = ${POOL}/providers/github"
echo "GCP_SERVICE_ACCOUNT = ${SA}"
```

## 6. Segredos no GitHub

Os dois valores impressos acima, mais as credenciais da OCI:

```bash
gh secret set GCP_WIF_PROVIDER --body "${POOL}/providers/github"
gh secret set GCP_SERVICE_ACCOUNT --body "$SA"

# OCI: os quatro primeiros saem do ~/.oci/config
gh secret set OCI_CLI_USER        --body "$(awk -F= '/^user=/{print $2}' ~/.oci/config)"
gh secret set OCI_CLI_TENANCY     --body "$(awk -F= '/^tenancy=/{print $2}' ~/.oci/config)"
gh secret set OCI_CLI_FINGERPRINT --body "$(awk -F= '/^fingerprint=/{print $2}' ~/.oci/config)"
gh secret set OCI_CLI_REGION      --body "$(awk -F= '/^region=/{print $2}' ~/.oci/config)"
gh secret set OCI_BUCKET          --body "RAGnaldo-sources"

# A chave privada é multilinha: vai por arquivo, nunca por --body.
gh secret set OCI_CLI_KEY_CONTENT < ~/.oci/ragnaldo_api_key.pem
```

Conferir sem revelar valores:

```bash
gh secret list
```

## 7. Primeiro deploy

```bash
gh workflow run deploy
gh run watch
```

A URL pública aparece no resumo da execução.

## Depois que estiver no ar

```bash
gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'
```

Sobre custo: o serviço sobe com `--max-instances 3` e sem instância mínima, então
não há cobrança enquanto ninguém acessa. O preço é o cold start — carregar torch,
o modelo de embeddings e o índice leva dezenas de segundos. A landing page com
carregamento sob demanda existe exatamente para que essa espera aconteça depois
de um clique consciente, e não numa tela branca.

Se durante a avaliação a espera incomodar:

```bash
gcloud run services update "$SERVICE" --region "$REGION" --min-instances 1
```

Isso mantém uma instância quente e passa a custar por hora, ininterruptamente.
Vale ligar na véspera da entrega e desligar depois.
