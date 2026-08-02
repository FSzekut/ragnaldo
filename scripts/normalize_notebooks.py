"""Adiciona IDs determinísticos às células sem alterar código ou outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]


def cell_id(notebook_name: str, position: int, source: str) -> str:
    identity = f"{notebook_name}|{position}|{source}".encode()
    return hashlib.sha256(identity).hexdigest()[:12]


def main() -> None:
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(path, as_version=4)
        for position, cell in enumerate(notebook.cells):
            cell["id"] = cell_id(path.name, position, cell.get("source", ""))
        nbformat.write(notebook, path)
        print(f"normalizado: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
