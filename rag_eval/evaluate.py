"""Score the live library search with Hit@5, MRR, and retrieval latency.

Uses the same search as chat: the first 5 chunks for one user. A retrieved
chunk is relevant when it contains the question's evidence passage or its
text hash matches a labeled chunk. Overlap may mark two chunks relevant;
the first of them fixes the reciprocal rank.

The corpus files must already be indexed for that user. From backend:

    .venv\\Scripts\\python.exe ..\\rag_eval\\evaluate.py --user-id 1
    .venv\\Scripts\\python.exe ..\\rag_eval\\evaluate.py --user-id 1 --save --message "baseline"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = Path(__file__).resolve().parent / "benchmarks.md"
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


def append_result(message: str, lines: list[str]) -> None:
    parts = [message.strip()] if message.strip() else []
    parts.extend(lines)
    with LOG.open("a", encoding="utf-8") as log:
        log.write("\n".join(parts) + "\n\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute Hit@5, MRR, and retrieval latency for rag_eval/questions.json")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--questions", type=Path, default=Path(__file__).resolve().parent / "questions.json")
    parser.add_argument("--save", action="store_true", help="Append the summary and optional message to rag_eval/benchmarks.md")
    parser.add_argument("--message", default="", help="Note written above the summary when --save is set")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.search import search_chunks

    payload = json.loads(args.questions.read_text(encoding="utf-8"))
    questions = payload["questions"]
    hits_total = 0
    reciprocal_total = 0.0
    latencies: list[float] = []
    corpus_seen = False
    corpus_names = {item["file"] for item in payload["files"]}

    search_chunks("прогрев", args.user_id)

    for question in questions:
        started = time.perf_counter()
        found = search_chunks(question["question"], args.user_id)[:K]
        elapsed = time.perf_counter() - started
        latencies.append(elapsed)
        corpus_seen = corpus_seen or any(hit.title in corpus_names for hit in found)
        hit, reciprocal = score(question, found)
        hits_total += hit
        reciprocal_total += reciprocal
        rank = next((item.rank for item in found if relevant(item.text, question)), None)
        print(f"{question['id']}  hit={hit}  rank={rank if rank else '-'}  {elapsed * 1000:.0f} ms  {question['file']}", flush=True)

    count = len(questions)
    ordered = sorted(latencies)
    mean = sum(ordered) / count
    p50 = ordered[min(count - 1, int(0.50 * count))]
    p95 = ordered[min(count - 1, int(0.95 * count))]
    summary = [
        f"Hit@{K}  {hits_total / count:.3f}  ({hits_total}/{count})",
        f"MRR@{K}  {reciprocal_total / count:.3f}",
        f"Latency  mean {mean * 1000:.0f} ms   p50 {p50 * 1000:.0f} ms   p95 {p95 * 1000:.0f} ms",
    ]
    if not corpus_seen:
        summary.append("None of the retrieved chunks come from rag_eval/corpus. Index those files for this user before reading the scores.")
    for line in summary:
        print(line, flush=True)
    if args.save:
        append_result(args.message, summary)


if __name__ == "__main__":
    main()
