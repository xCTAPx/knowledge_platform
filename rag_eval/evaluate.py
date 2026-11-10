"""Score the live library search with Hit@5, MRR@5, Recall@5, NDCG@5, Precision@5, and retrieval latency.

`--mode hybrid` is the chat search. `dense` and `bm25` each return their own top 5.
`dense_rerank` reranks the twenty nearest Qdrant chunks and keeps five.
A retrieved chunk is relevant when it contains the question's evidence passage
or its text hash matches a labeled chunk. Twelve questions label two chunks.
The first relevant hit fixes the reciprocal rank.

The corpus files must already be indexed for that user. From backend:

    .venv\\Scripts\\python.exe ..\\rag_eval\\evaluate.py --user-id 1
    .venv\\Scripts\\python.exe ..\\rag_eval\\evaluate.py --user-id 1 --mode dense --save --message "qdrant"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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


def score(question: dict, hits: list) -> tuple[int, float, float, float, float]:
    gains = [1.0 if relevant(hit.text, question) else 0.0 for hit in hits[:K]]
    hit = 1 if any(gains) else 0
    reciprocal = next((1 / rank for rank, gain in enumerate(gains, start=1) if gain), 0.0)
    found = int(sum(gains))
    labeled = len(question["relevant_chunks"])
    recall_den = labeled or found
    recall = min(1.0, found / recall_den) if recall_den else 0.0
    precision = found / K
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))
    ideal = min(K, labeled or found)
    idcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal + 1))
    return hit, reciprocal, recall, dcg / idcg if idcg else 0.0, precision


def append_result(message: str, lines: list[str]) -> None:
    parts = [message.strip()] if message.strip() else []
    parts.extend(lines)
    with LOG.open("a", encoding="utf-8") as log:
        log.write("\n".join(parts) + "\n\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute retrieval metrics for rag_eval/questions.json")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--mode", choices=["dense", "dense_rerank", "bm25", "hybrid"], default="hybrid")
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
    recall_total = 0.0
    ndcg_total = 0.0
    precision_total = 0.0
    latencies: list[float] = []
    corpus_seen = False
    corpus_names = {item["file"] for item in payload["files"]}

    search_chunks("прогрев", args.user_id, args.mode)

    for question in questions:
        started = time.perf_counter()
        found = search_chunks(question["question"], args.user_id, args.mode)[:K]
        elapsed = time.perf_counter() - started
        latencies.append(elapsed)
        corpus_seen = corpus_seen or any(hit.title in corpus_names for hit in found)
        hit, reciprocal, recall, ndcg, precision = score(question, found)
        hits_total += hit
        reciprocal_total += reciprocal
        recall_total += recall
        ndcg_total += ndcg
        precision_total += precision
        rank = next((place for place, item in enumerate(found, start=1) if relevant(item.text, question)), None)
        print(
            f"{question['id']}  hit={hit}  rank={rank if rank else '-'}  "
            f"recall={recall:.3f}  ndcg={ndcg:.3f}  precision={precision:.3f}  "
            f"{elapsed * 1000:.0f} ms  {question['file']}",
            flush=True,
        )

    count = len(questions)
    ordered = sorted(latencies)
    mean = sum(ordered) / count
    p50 = ordered[min(count - 1, int(0.50 * count))]
    p95 = ordered[min(count - 1, int(0.95 * count))]
    summary = [
        f"mode  {args.mode}",
        f"Hit@{K}  {hits_total / count:.3f}  ({hits_total}/{count})",
        f"MRR@{K}  {reciprocal_total / count:.3f}",
        f"Recall@{K}  {recall_total / count:.3f}",
        f"NDCG@{K}  {ndcg_total / count:.3f}",
        f"Precision@{K}  {precision_total / count:.3f}",
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
