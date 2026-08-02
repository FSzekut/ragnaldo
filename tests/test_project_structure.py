import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_notebooks_are_valid_json_and_use_ragnaldo_kernel():
    notebooks = sorted((ROOT / "notebooks").glob("*.ipynb"))
    assert len(notebooks) == 5
    for notebook in notebooks:
        content = json.loads(notebook.read_text(encoding="utf-8"))
        assert content["nbformat"] == 4
        assert content["metadata"]["kernelspec"]["name"] == "ragnaldo"
        cell_ids = [cell.get("id") for cell in content["cells"]]
        assert all(cell_ids)
        assert len(cell_ids) == len(set(cell_ids))


def test_source_manifest_targets_stay_inside_data():
    # Um target absoluto ou com ".." faria o downloader escrever fora do projeto.
    # "raw" guarda o arquivo como veio da origem; "processed", o que foi convertido.
    manifest = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    for source in manifest["sources"] + manifest["derived_sources"]:
        target = Path(source["target"])
        assert not target.is_absolute()
        assert ".." not in target.parts
        assert target.parts[0] == "data"
        assert target.parts[1] in {"raw", "processed"}


def test_downloader_only_handles_directly_fetchable_sources():
    # download_sources.py faz um GET simples e compara o hash. As fontes derivadas
    # vêm de API e conversão: se entrassem em "sources", o script baixaria a página
    # errada, o hash não bateria e ele apagaria o arquivo.
    manifest = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    assert all("fetch" not in source for source in manifest["sources"])
    assert all(source["fetch"] == "api-json" for source in manifest["derived_sources"])

    ids = [source["id"] for source in manifest["sources"] + manifest["derived_sources"]]
    assert len(ids) == len(set(ids))


def test_secret_files_are_ignored():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    assert ".streamlit/secrets.toml" in gitignore
    assert "env/" in gitignore
