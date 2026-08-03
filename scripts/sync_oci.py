"""Sincroniza os documentos-fonte com o OCI Object Storage.

Os diretórios data/raw e data/processed ficam fora do Git: são conteúdo de
terceiros, e o repositório é público. Isso resolve a licença e cria um problema
de pipeline — quem clona o projeto, inclusive o CI, não recebe os documentos e
não consegue reconstruir o índice.

O bucket é a resposta: guarda os originais, o CI baixa antes do build. É também
o serviço OCI que o card 7 do enunciado descreve ("os arquivos originais ficam
no OCI Object Storage").

Uso:
    python scripts/sync_oci.py upload
    python scripts/sync_oci.py download
    python scripts/sync_oci.py status

Autenticação: variáveis OCI_CLI_* quando presentes (é o caso do GitHub Actions),
senão ~/.oci/config. Nenhuma credencial fica no repositório.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUCKET = os.getenv("OCI_BUCKET", "RAGnaldo-sources")

# Prefixo no bucket -> diretório local. Mantém a mesma separação que existe em
# disco: o que veio como veio, e o que precisou de conversão.
SYNCED_DIRS = {
    "raw": ROOT / "data" / "raw",
    "processed": ROOT / "data" / "processed",
}

# O Object Storage calcula MD5 sozinho, mas o projeto inteiro fala SHA-256
# (manifesto de fontes, manifesto do índice). Guardar o mesmo algoritmo como
# metadado do objeto evita ter duas noções de "esse arquivo mudou".
SHA_METADATA_KEY = "sha256"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_config() -> dict:
    """Credenciais do ambiente quando houver; do arquivo local caso contrário.

    No CI não existe ~/.oci/config, e escrever a chave privada em disco durante
    o build só cria um arquivo a mais para vazar. O SDK aceita o conteúdo da
    chave direto em memória, que é o caminho usado quando as variáveis existem.
    """
    import oci

    if os.getenv("OCI_CLI_USER"):
        config = {
            "user": os.environ["OCI_CLI_USER"],
            "tenancy": os.environ["OCI_CLI_TENANCY"],
            "fingerprint": os.environ["OCI_CLI_FINGERPRINT"],
            "region": os.environ["OCI_CLI_REGION"],
            "key_content": os.environ["OCI_CLI_KEY_CONTENT"],
        }
    else:
        config = oci.config.from_file()

    oci.config.validate_config(config)
    return config


def get_client():
    import oci

    return oci.object_storage.ObjectStorageClient(build_config())


def remote_objects(client, namespace: str) -> dict[str, str]:
    """Mapeia nome do objeto -> sha256 registrado nos metadados."""
    import oci

    found: dict[str, str] = {}
    for prefix in SYNCED_DIRS:
        start = None
        while True:
            response = client.list_objects(
                namespace, BUCKET, prefix=f"{prefix}/", start=start, fields="name"
            )
            for item in response.data.objects:
                try:
                    head = client.head_object(namespace, BUCKET, item.name)
                except oci.exceptions.ServiceError:
                    continue
                metadata = {k.lower(): v for k, v in (head.headers or {}).items()}
                found[item.name] = metadata.get(f"opc-meta-{SHA_METADATA_KEY}", "")
            start = response.data.next_start_with
            if not start:
                break
    return found


def local_files() -> dict[str, Path]:
    """Mapeia nome do objeto -> caminho local, ignorando ocultos e .gitkeep."""
    found: dict[str, Path] = {}
    for prefix, directory in SYNCED_DIRS.items():
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            found[f"{prefix}/{path.relative_to(directory).as_posix()}"] = path
    return found


def upload(client, namespace: str) -> None:
    remote = remote_objects(client, namespace)
    local = local_files()
    if not local:
        print("Nada em data/raw ou data/processed. Rode scripts/download_sources.py antes.")
        return

    enviados = ignorados = 0
    for name, path in local.items():
        digest = sha256_file(path)
        if remote.get(name) == digest:
            print(f"  = {name} (inalterado)")
            ignorados += 1
            continue
        with path.open("rb") as handle:
            client.put_object(
                namespace,
                BUCKET,
                name,
                handle,
                opc_meta={SHA_METADATA_KEY: digest},
            )
        tamanho = path.stat().st_size / 1024
        print(f"  ^ {name} ({tamanho:.0f} KB)")
        enviados += 1

    print(f"\n{enviados} enviado(s), {ignorados} inalterado(s) em {BUCKET}.")


def download(client, namespace: str) -> None:
    remote = remote_objects(client, namespace)
    if not remote:
        print(f"Bucket {BUCKET} vazio. Rode 'upload' de uma máquina que tenha as fontes.")
        return

    baixados = ignorados = 0
    for name, digest_remoto in sorted(remote.items()):
        prefix, _, relativo = name.partition("/")
        destino = SYNCED_DIRS[prefix] / relativo

        if destino.exists() and digest_remoto and sha256_file(destino) == digest_remoto:
            print(f"  = {name} (inalterado)")
            ignorados += 1
            continue

        destino.parent.mkdir(parents=True, exist_ok=True)
        response = client.get_object(namespace, BUCKET, name)
        with destino.open("wb") as handle:
            for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
                handle.write(chunk)

        # Um download truncado produz um arquivo válido e menor, que a ingestão
        # aceitaria sem reclamar e indexaria pela metade.
        if digest_remoto and sha256_file(destino) != digest_remoto:
            destino.unlink(missing_ok=True)
            raise RuntimeError(f"Hash divergente em {name}. Arquivo removido.")

        print(f"  v {name}")
        baixados += 1

    print(f"\n{baixados} baixado(s), {ignorados} inalterado(s).")


def status(client, namespace: str) -> None:
    remote = remote_objects(client, namespace)
    local = local_files()

    print(f"bucket: {BUCKET} | objetos remotos: {len(remote)} | arquivos locais: {len(local)}\n")
    for name in sorted(set(remote) | set(local)):
        if name not in remote:
            marca = "só local"
        elif name not in local:
            marca = "só remoto"
        elif remote[name] == sha256_file(local[name]):
            marca = "sincronizado"
        else:
            marca = "DIFERENTE"
        print(f"  {marca:14} {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["upload", "download", "status"])
    args = parser.parse_args()

    try:
        client = get_client()
    except Exception as error:  # noqa: BLE001
        print(f"Falha ao autenticar na OCI: {error}", file=sys.stderr)
        print(
            "Configure ~/.oci/config ou as variáveis OCI_CLI_USER, OCI_CLI_TENANCY, "
            "OCI_CLI_FINGERPRINT, OCI_CLI_REGION e OCI_CLI_KEY_CONTENT.",
            file=sys.stderr,
        )
        return 1

    namespace = os.getenv("OCI_NAMESPACE") or client.get_namespace().data
    {"upload": upload, "download": download, "status": status}[args.action](client, namespace)
    return 0


if __name__ == "__main__":
    sys.exit(main())
