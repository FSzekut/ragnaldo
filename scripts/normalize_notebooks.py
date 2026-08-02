"""Deixa os notebooks em estado publicável, sem alterar código ou resultados.

Três coisas que a execução desarruma e que ninguém lembra de conferir:

1. IDs de célula, que precisam ser estáveis para o diff ser legível;
2. o kernelspec, que volta para "python3" quando o notebook roda por um kernel
   diferente do declarado (o VS Code e o Jupyter fazem isso sem avisar);
3. outputs de stderr, que carregam avisos de ambiente com o caminho absoluto da
   máquina de quem executou — em repositório público, isso vira o username de
   alguém.

Nenhuma delas quebra a execução, e é por isso que passam despercebidas.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
KERNEL_NAME = "ragnaldo"
KERNEL_DISPLAY = "Python (RAGnaldo)"


def cell_id(notebook_name: str, position: int, source: str) -> str:
    identity = f"{notebook_name}|{position}|{source}".encode()
    return hashlib.sha256(identity).hexdigest()[:12]


def strip_stderr(cell) -> int:
    outputs = cell.get("outputs")
    if not outputs:
        return 0
    kept = [
        output
        for output in outputs
        if not (output.get("output_type") == "stream" and output.get("name") == "stderr")
    ]
    removed = len(outputs) - len(kept)
    cell["outputs"] = kept
    return removed


def main() -> None:
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(path, as_version=4)

        removed = 0
        for position, cell in enumerate(notebook.cells):
            cell["id"] = cell_id(path.name, position, cell.get("source", ""))
            if cell.get("cell_type") == "code":
                removed += strip_stderr(cell)

        kernelspec = notebook.metadata.get("kernelspec", {})
        restored = kernelspec.get("name") != KERNEL_NAME
        notebook.metadata["kernelspec"] = {
            "name": KERNEL_NAME,
            "display_name": KERNEL_DISPLAY,
            "language": "python",
        }

        nbformat.write(notebook, path)

        notes = []
        if removed:
            notes.append(f"{removed} output(s) de stderr removido(s)")
        if restored:
            notes.append(f"kernel restaurado de '{kernelspec.get('name')}'")
        suffix = f" — {'; '.join(notes)}" if notes else ""
        print(f"normalizado: {path.relative_to(ROOT)}{suffix}")


if __name__ == "__main__":
    main()
