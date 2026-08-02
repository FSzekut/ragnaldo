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


def test_source_manifest_targets_stay_inside_raw_data():
    manifest = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    for source in manifest["sources"]:
        target = Path(source["target"])
        assert not target.is_absolute()
        assert target.parts[:2] == ("data", "raw")


def test_secret_files_are_ignored():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    assert ".streamlit/secrets.toml" in gitignore
    assert "env/" in gitignore
