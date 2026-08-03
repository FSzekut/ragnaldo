"""Verifica se o agente responde o que sabe e recusa o que não sabe.

Um RAG quebra de duas formas opostas, e nenhuma delas gera exceção:

- silêncio indevido: a resposta está no corpus, mas o corte a descartou;
- resposta indevida: a pergunta é sobre algo que o corpus não cobre, e ele
  responde assim mesmo com o trecho menos ruim que encontrou.

Testes unitários não pegam nenhuma das duas, porque o código está correto nos
dois casos — o que está errado é a calibração. Este script executa perguntas
com expectativa declarada e falha quando a calibração regride.

Não é pytest porque depende do índice, que é grande e fica fora do Git. Roda
depois de scripts/build_index.py, tanto local quanto no CI.

Uso:
    python scripts/eval_retrieval.py
    python scripts/eval_retrieval.py --verbose
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ragnaldo.config import SETTINGS
from ragnaldo.generation import select_evidence
from ragnaldo.ingestion import load_verified_index

# (pergunta, deve encontrar evidência)
CASES: list[tuple[str, bool]] = [
    # Dentro do corpus, em linguagem coloquial: é assim que as pessoas perguntam,
    # e é onde a recuperação falhava quando k=4 e o limiar era absoluto.
    ("para quem é o programa ONE?", True),
    ("o que é o ONE AI for Tech?", True),
    ("quais são as fases da jornada?", True),
    ("o que o ONE ensina sobre RAG e LangChain?", True),
    ("quais os requisitos do Challenge?", True),
    ("preciso fazer deploy em qual nuvem?", True),
    ("como funciona o lazy loading do RAGnaldo?", True),
    ("por que os embeddings são locais?", True),
    # Sobre o próprio acervo: só funcionam porque existe um documento que
    # descreve o corpus. Busca por similaridade não enumera o que ela indexa.
    ("que tipo de informação você tem?", True),
    ("sobre o que posso perguntar?", True),
    ("o que você sabe?", True),
    # Sobre a própria identidade. Falhavam quando o dossiê só descrevia o
    # RAGnaldo em terceira pessoa: "RAGnaldo é um guia" fica longe de "quem é
    # você?". Quem pergunta usa a segunda pessoa, e o texto precisa acompanhar.
    ("quem é você?", True),
    ("como você foi construído?", True),
    ("que tecnologias você usa?", True),
    # Fora do corpus: aqui a resposta correta é o silêncio.
    ("Qual foi o placar da final da Copa do Mundo de 1970?", False),
    ("Qual a receita de bolo de cenoura?", False),
    ("Quem é o presidente da França?", False),
    ("Como declarar imposto de renda?", False),
    ("Quanto custa uma passagem para Lisboa?", False),
]

# Um caso removido de propósito: "qual o melhor investimento para 2026?" passa
# pelo corte com distância 1.02, e está certo que passe — o relatório da Oracle
# discute investimento em IA e retorno, então existe sinal real. Quem precisa
# recusar ali é o modelo, que recebe o contexto e vê que ele responde sobre
# outro tipo de investimento. O corte é grosseiro por natureza: ele decide se há
# assunto, não se há resposta. Esperar dele a distinção fina seria calibrá-lo
# apertado a ponto de descartar as perguntas legítimas de novo.


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", action="store_true", help="Mostra os trechos aceitos.")
    args = parser.parse_args()

    vector_store, manifest = load_verified_index()
    print(f"{manifest['chunk_count']} chunks | k={SETTINGS.retrieval_k}\n")

    falhas = []
    for question, deve_responder in CASES:
        results = vector_store.similarity_search_with_score(question, k=SETTINGS.retrieval_k)
        evidence = select_evidence(results)
        respondeu = bool(evidence)
        melhor = min(score for _, score in results) if results else float("inf")

        if respondeu != deve_responder:
            falhas.append(question)
            marca = "FALHOU"
        else:
            marca = "ok    "

        acao = "responde" if respondeu else "recusa  "
        print(f"{marca} {acao} melhor={melhor:.3f} aceitos={len(evidence):2}  {question}")

        if args.verbose:
            for document, score in evidence:
                fonte = document.metadata.get("source", "?")
                print(f"           {score:.3f} {fonte[:30]:30} {document.page_content[:60].strip()}")

    print(f"\n{len(CASES) - len(falhas)}/{len(CASES)} corretos")
    if falhas:
        print("\nCasos que regrediram:", file=sys.stderr)
        for question in falhas:
            print(f"  - {question}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
