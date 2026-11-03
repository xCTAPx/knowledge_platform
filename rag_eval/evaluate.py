"""Score the live library search with Hit@5 and MRR.

Uses the same search as chat: the first 5 chunks for one user. A retrieved
chunk is relevant when it contains the question's evidence passage or its
text hash matches a labeled chunk. Overlap may mark two chunks relevant;
the first of them fixes the reciprocal rank.

The corpus files must already be indexed for that user. From backend:

    .venv\\Scripts\\python.exe ..\\rag_eval\\evaluate.py --user-id 1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K = 5


def relevant(hit_text: str, question: dict) -> bool:
    if question["evidence"] in hit_text:
        return True
    digest = hashlib.sha256(hit_text.encode()).hexdigest()
    return any(digest == item["chunk_sha256"] for item in question["relevant_chunks"])


def score(question: dict, hits: list) -> tuple[int, float]:
    for hit in hits[:K]:
        if relevant(hit.text, question):
            return 1, 1 / hit.rank
    return 0, 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute Hit@5 and MRR for rag_eval/questions.json")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--questions", type=Path, default=Path(__file__).resolve().parent / "questions.json")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.vectors import search_chunks

    payload = json.loads(args.questions.read_text(encoding="utf-8"))
    questions = payload["questions"]
    hits_total = 0
    reciprocal_total = 0.0
    corpus_seen = False
    corpus_names = {item["file"] for item in payload["files"]}

    for question in questions:
        found = search_chunks(question["question"], args.user_id)[:K]
        corpus_seen = corpus_seen or any(hit.title in corpus_names for hit in found)
        hit, reciprocal = score(question, found)
        hits_total += hit
        reciprocal_total += reciprocal
        rank = next((item.rank for item in found if relevant(item.text, question)), None)
        print(f"{question['id']}  hit={hit}  rank={rank if rank else '-'}  {question['file']}")

    count = len(questions)
    print(f"Hit@{K}  {hits_total / count:.3f}  ({hits_total}/{count})")
    print(f"MRR@{K}  {reciprocal_total / count:.3f}")
    if not corpus_seen:
        print("None of the retrieved chunks come from rag_eval/corpus. Index those files for this user before reading the scores.")


if __name__ == "__main__":
    main()
