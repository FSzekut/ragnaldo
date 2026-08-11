"""Torna o pacote em src/ importável durante os testes.

O projeto não é instalado como pacote: cada entrypoint (app/main.py,
scripts/build_index.py, scripts/eval_retrieval.py) insere src/ no sys.path
equivalente disso para a suíte — o pytest o carrega antes da coleta,
então vale para qualquer teste novo sem repetir o truque em cada um.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))