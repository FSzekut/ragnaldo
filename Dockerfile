# Imagem de produção do RAGnaldo.
#
# Só o serving entra aqui. Os parsers de PDF, Word, Excel e PowerPoint ficam de
# fora: eles pertencem à ingestão, que roda antes do build. O que a aplicação
# precisa é do índice já pronto e do modelo de embeddings para vetorizar a
# pergunta do usuário.

FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE: .pyc em container é lixo que só engorda a camada.
# PYTHONUNBUFFERED: sem isso o log do Cloud Run aparece em blocos atrasados.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HF_HOME=/opt/hf-cache \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# O watcher percorre todo módulo carregado procurando arquivo para vigiar, e o
# transformers importa dezenas de processadores de imagem que dependem de
# torchvision — ausente, porque instalamos apenas o torch. Nada disso é usado,
# mas cada tentativa imprime um traceback no log. Em container não há código
# mudando para vigiar.
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

WORKDIR /app

# O PyTorch do PyPI traz as bibliotecas CUDA junto: vários gigabytes de suporte
# a GPU para uma aplicação que roda em CPU. O índice oficial dá a versão limpa.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# O modelo é baixado no build, não no primeiro acesso. Sem isso, a primeira
# pessoa a abrir o app depois de cada instância nova esperaria o download de
# ~120 MB — e uma falha de rede no Cloud Run viraria erro na cara do usuário.
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Depois do modelo já estar na imagem, qualquer consulta ao Hub é round-trip
# inútil no caminho crítico do cold start — e transforma indisponibilidade da
# rede em falha de inicialização. Só pode vir depois do RUN acima, que precisa
# justamente baixar o modelo.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

COPY src/ ./src/
COPY app/ ./app/
# Gerado por scripts/build_index.py antes do build. Ver .dockerignore.
COPY artifacts/vector_store/ ./artifacts/vector_store/

# O Cloud Run injeta PORT e espera que o processo escute nele. Fixar 8080 no
# comando funcionaria hoje e quebraria no dia em que a plataforma mudar.
ENV PORT=8080
EXPOSE 8080

# Forma JSON para o sinal de parada chegar ao processo (sem ela, o shell vira
# PID 1 e engole o SIGTERM que o Cloud Run manda ao desligar a instância). O
# "sh -c" continua necessário para expandir ${PORT}, e o "exec" faz o streamlit
# substituir o shell em vez de virar seu filho.
CMD ["sh", "-c", "exec streamlit run app/main.py --server.port=${PORT} --server.address=0.0.0.0"]
