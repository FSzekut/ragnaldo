"""Bloqueia commits com sinais comuns de segredos ou arquivos indevidos."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_STAGED_FILE_BYTES = 10 * 1024 * 1024
FORBIDDEN_NAMES = {".env", "secrets.toml", "credentials.json", "service-account.json"}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
SECRET_PATTERNS = {
    "OpenAI-like token": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Anthropic API key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
}

# Não é segredo, mas identifica a máquina de quem executou. Chega quase sempre
# por output de notebook: um aviso de biblioteca em stderr traz o caminho do
# site-packages junto, e ninguém revisa output que não mudou o resultado.
HOME_PATH_PATTERN = re.compile(r"(?:/home/|/Users/|[A-Za-z]:\\Users\\)[A-Za-z0-9_.-]+[/\\]")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def staged_files() -> list[Path]:
    output = git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [ROOT / line for line in output.splitlines() if line]


def main() -> int:
    failures: list[str] = []
    files = staged_files()
    if not files:
        print("SECURITY CHECK: nenhum arquivo staged; nenhum commit deve ser criado.")
        return 1

    for path in files:
        relative = path.relative_to(ROOT)
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            failures.append(f"arquivo sensível staged: {relative}")
            continue
        if not path.exists():
            continue
        if path.stat().st_size > MAX_STAGED_FILE_BYTES:
            failures.append(f"arquivo staged acima de 10 MiB: {relative}")
            continue
        if b"\x00" in path.read_bytes()[:8192]:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"possível {label}: {relative}")

        if found := HOME_PATH_PATTERN.search(text):
            hint = (
                " (rode scripts/normalize_notebooks.py)"
                if path.suffix == ".ipynb"
                else ""
            )
            failures.append(f"caminho absoluto de usuário em {relative}: {found.group()}{hint}")

    diff_check = subprocess.run(
        ["git", "diff", "--cached", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if diff_check.returncode:
        failures.append(f"git diff --check falhou:\n{diff_check.stdout}{diff_check.stderr}")

    if failures:
        print("SECURITY CHECK: FALHOU")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"SECURITY CHECK: OK ({len(files)} arquivos staged verificados)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
