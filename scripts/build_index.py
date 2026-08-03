"""Gera o índice vetorial sem depender do Jupyter.

O notebook 01 é o lugar de entender o pipeline; este script é o de executá-lo
sem supervisão. Ambos chamam exatamente as mesmas funções de ragnaldo.ingestion,
então não existe a possibilidade de o índice do CI ser construído por um caminho
diferente do que foi validado à mão.

Uso:
    python scripts/build_index.py
    python scripts/build_index.py --skip manual_one_historico.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ragnaldo.config import (
    AUTHORIAL_SOURCES_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    VECTOR_STORE_DIR,
)
from ragnaldo.ingestion import (
    build_index,
    discover_sources,
    load_sources,
    split_documents,
)

# O manual histórico descreve regras de edições anteriores do programa. Indexá-lo
# faria o agente responder prazos vencidos com a mesma confiança dos atuais.
DEFAULT_SKIP = ["manual_one_historico.pdf"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--skip",
        nargs="*",
        default=DEFAULT_SKIP,
        help="Nomes de arquivo a excluir do corpus.",
    )
    args = parser.parse_args()
    ignorados = set(args.skip)

    paths = [
        path
        for path in discover_sources(RAW_DATA_DIR, PROCESSED_DATA_DIR, AUTHORIAL_SOURCES_DIR)
        if path.name not in ignorados
    ]
    if not paths:
        print(
            "Nenhuma fonte encontrada. Rode scripts/sync_oci.py download "
            "ou scripts/download_sources.py antes.",
            file=sys.stderr,
        )
        return 1

    print(f"{len(paths)} fonte(s):")
    for path in paths:
        print(f"  {path.relative_to(ROOT)}")
    if ignorados:
        print(f"ignoradas por --skip: {', '.join(sorted(ignorados))}")

    documents = load_sources(paths)
    chunks = split_documents(documents)
    print(f"\n{len(documents)} documento(s) -> {len(chunks)} chunk(s)")
    print("Gerando embeddings (modelo local, CPU)...")

    manifest = build_index(chunks, VECTOR_STORE_DIR)
    print(f"\nÍndice em {VECTOR_STORE_DIR.relative_to(ROOT)}")
    print(f"  modelo: {manifest['embedding_model']}")
    print(f"  chunks: {manifest['chunk_count']}")
    print(f"  fontes: {len(manifest['source_hashes'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
