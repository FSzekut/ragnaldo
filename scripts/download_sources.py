"""Baixa as fontes públicas declaradas em data/sources.json.

Arquivos de terceiros permanecem fora do Git. O manifesto preserva URL,
procedência, data da pesquisa e hash observado para tornar a ingestão reproduzível.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "sources.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "RAGnaldo/0.1 source-fetcher"})
    with urlopen(request, timeout=60) as response, target.open("wb") as output:
        while block := response.read(1024 * 1024):
            output.write(block)


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for source in manifest["sources"]:
        target = ROOT / source["target"]
        print(f"Baixando {source['title']} -> {target.relative_to(ROOT)}")
        download(source["url"], target)
        observed = sha256_file(target)
        expected = source.get("sha256")

        if expected and observed != expected:
            if source["status"] == "mutable-web-snapshot":
                print(f"  AVISO: a página mudou. Hash atual: {observed}")
            else:
                target.unlink(missing_ok=True)
                raise RuntimeError(
                    f"Hash inesperado para {source['id']}: {observed}. "
                    "O arquivo foi removido por segurança."
                )
        else:
            print(f"  OK: {observed}")


if __name__ == "__main__":
    main()
