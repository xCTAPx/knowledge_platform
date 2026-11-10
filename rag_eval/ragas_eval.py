"""Score generated answers with RAGAS.

Answers are produced by the same prompt as chat: one user turn, the library
excerpts from search, and the system instruction inside stream. RAGAS then
judges that finished text. It does not search or answer again.

From backend:

    .venv\\Scripts\\python.exe ..\\rag_eval\\ragas_eval.py --user-id 1
    .venv\\Scripts\\python.exe ..\\rag_eval\\ragas_eval.py --user-id 1 --save --message "ragas"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

print("ragas_eval: loading libraries", flush=True)
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI

ROOT = Path(__file__).resolve().parents[1]
LOG = Path(__file__).resolve().parent / "benchmarks.md"
ANSWERS = Path(__file__).resolve().parent / "answers.json"
BACKEND = ROOT / "backend"


class LocalEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        from app.core.embeddings import embed

        return [list(map(float, row)) for row in embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def append_result(message: str, lines: list[str]) -> None:
    parts = [message.strip()] if message.strip() else []
    parts.extend(lines)
    with LOG.open("a", encoding="utf-8") as log:
        log.write("\n".join(parts) + "\n\n")


def load_answers() -> dict[str, dict]:
    if not ANSWERS.exists():
        return {}
    saved = json.loads(ANSWERS.read_text(encoding="utf-8"))
    return {f"{item.get('mode', '')}\n{item['question']}": item for item in saved}


def store_answers(saved: dict[str, dict]) -> None:
    ANSWERS.write_text(
        json.dumps(list(saved.values()), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def answer(question: str, user_id: int) -> tuple[str, list[str]]:
    from app.core.library import library_prompt
    from app.core.llm import stream
    from app.core.search import search_chunks

    contexts = [hit.text for hit in search_chunks(question, user_id)]
    prompt = library_prompt(f"user: {question}", "\n\n".join(contexts))
    return b"".join(stream(prompt, max_tokens=1024)).decode(), contexts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate chat answers and score them with RAGAS")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--questions", type=Path, default=Path(__file__).resolve().parent / "questions.json")
    parser.add_argument("--limit", type=int, default=0, help="Score only the first N questions")
    parser.add_argument("--save", action="store_true", help="Append the summary and optional message to rag_eval/benchmarks.md")
    parser.add_argument("--message", default="", help="Note written above the summary when --save is set")
    args = parser.parse_args()

    print("ragas_eval: loading search", flush=True)
    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    from app.core.config import settings
    from app.core.search import MODE

    if not settings.llm_api_key:
        raise SystemExit("LLM_API_KEY is empty. RAGAS needs the same key the chat uses.")

    payload = json.loads(args.questions.read_text(encoding="utf-8"))
    questions = payload["questions"]
    if args.limit > 0:
        questions = questions[: args.limit]

    print(f"mode  {MODE}", flush=True)
    saved = load_answers()
    rows: dict[str, list] = {"user_input": [], "response": [], "retrieved_contexts": [], "reference": []}
    for question in questions:
        text_q = question["question"]
        cached = saved.get(f"{MODE}\n{text_q}")
        if cached is not None and cached.get("evidence") == question["evidence"] and cached.get("mode") == MODE:
            text, contexts = cached["response"], cached["contexts"]
            print(f"{question['id']}  cached", flush=True)
        else:
            print(f"{question['id']}  searching", flush=True)
            text, contexts = answer(text_q, args.user_id)
            saved[f"{MODE}\n{text_q}"] = {
                "mode": MODE,
                "question": text_q,
                "evidence": question["evidence"],
                "response": text,
                "contexts": contexts,
            }
            store_answers(saved)
            preview = text.replace("\n", " ")[:120]
            print(f"{question['id']}  {preview}", flush=True)
        rows["user_input"].append(text_q)
        rows["response"].append(text)
        rows["retrieved_contexts"].append(contexts)
        rows["reference"].append(question["evidence"])

    from datasets import Dataset
    from ragas import evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.run_config import RunConfig
    from ragas.metrics import (
        Faithfulness,
        FactualCorrectness,
        LLMContextPrecisionWithReference,
        LLMContextRecall,
        ResponseRelevancy,
    )

    judge = LangchainLLMWrapper(
        ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=0,
            max_tokens=1024,
            default_headers={"HTTP-Referer": settings.frontend_origin, "X-Title": settings.app_name},
        )
    )
    embeddings = LangchainEmbeddingsWrapper(LocalEmbeddings())
    result = evaluate(
        Dataset.from_dict(rows),
        metrics=[
            Faithfulness(),
            ResponseRelevancy(),
            LLMContextPrecisionWithReference(),
            LLMContextRecall(),
            FactualCorrectness(),
        ],
        llm=judge,
        embeddings=embeddings,
        raise_exceptions=True,
        run_config=RunConfig(timeout=600, max_workers=1, max_wait=120),
    )
    summary = [f"mode  {MODE}"] + [f"{name}  {float(value):.3f}" for name, value in result._repr_dict.items()]
    for line in summary:
        print(line, flush=True)
    if args.save:
        append_result(args.message, summary)


if __name__ == "__main__":
    main()
