# Knowledge Platform

A personal library with a chat over your own notes and files.

You register, keep notes and attachments in one tape, and ask questions in a saved chat. The answer is streamed from an OpenAI-compatible LLM. Before the call, search adds five chunks to the prompt. The active search is the single assignment to `MODE` in `backend/app/core/search.py`.

- Backend: FastAPI, PostgreSQL, Qdrant, Redis
- Frontend: React, TypeScript, Vite
- Embeddings: `BAAI/bge-m3` on CUDA, then `BAAI/bge-reranker-v2-m3`

## Requirements

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Docker, for Qdrant and Redis
- An NVIDIA GPU. The API loads the embedder and the reranker on `cuda:0`. The indexing worker loads a second copy of the embedder

## Backend

Create the database named in `DATABASE_URL`, then:

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env # if needed
alembic upgrade head
docker compose up -d
uvicorn app.main:app --reload --port 8000
```

In a second terminal, from `backend`, start the indexing worker. Uploads and note saves stay pending until this process is running:

```bash
# Windows
.venv\Scripts\python.exe -m app.worker

# macOS / Linux
.venv/bin/python -m app.worker
```

`copy` is the Windows command. On macOS and Linux, use `cp .env.example .env`.

In `.env`, replace `YOUR_PASSWORD` with the password you chose when installing PostgreSQL. That placeholder is not a real password: login fails with `password authentication failed for user "postgres"` until `DATABASE_URL` has the real one. Also set `JWT_SECRET` and `LLM_API_KEY`.

API docs: http://localhost:8000/docs  
Health check: http://localhost:8000/api/v1/health  
Qdrant dashboard: http://localhost:6333/dashboard — collection `chunks`

Saving a note or uploading a file stores the row and queues indexing in Redis. The API answers immediately. The card shows Indexing… until the worker finishes, then those chunks can be found in chat. After three failed attempts the card shows Could not index. A note is queued again when you save it. Redis keeps queued jobs if the API restarts. On worker startup, an empty `chunks` collection is queued for indexing. Refresh the library to see those cards change to Indexing…. Accepted uploads are PDF, txt, and Markdown, up to 10 MB. Text is split into chunks of 600 tokens with an overlap of 80. Search returns the 5 nearest chunks of the signed-in user.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

The dev server proxies `/api` to `http://localhost:8000`.

## Retrieval eval

`rag_eval/` holds six invented institutional archives, `healthcare_research.md`, and 40 questions whose relevant chunks are labeled in `questions.json`. The invented organizations, names, and figures do not exist outside this folder. Each question asks for a fact stated in its file and does not include the answer itself. Nearby drafts in the invented archives use similar names with wrong figures. `observatoriya_tikhy_kholm.txt` is a near-topic distractor and has no questions.

Upload those files into the library of the user you want to score, then from `backend`:

```bash
.venv\Scripts\python.exe ..\rag_eval\evaluate.py --user-id 1
```

`--mode dense` returns the five nearest Qdrant chunks. `--mode dense_rerank` reranks the twenty nearest Qdrant chunks and keeps five, without BM25. `--mode bm25` returns the five best BM25 chunks. `--mode hybrid` asks dense search and BM25 for twenty chunks each, then the reranker keeps five. That flag only selects the retrieval benchmark. Chat and `ragas_eval.py` follow `MODE`. Hit@5 is the share of questions whose labeled chunk appears in those five. MRR@5 is the average of `1 / rank` for the first labeled chunk, or 0 when it is missing. Recall@5 divides how many of the five are labeled by how many labeled chunks the question has. NDCG@5 uses the same binary labels and discounts lower ranks. Precision@5 divides the labeled hits by 5. Twelve questions ask for two facts from different chunks of the same file, and both chunks are labeled. On those, Recall@5 and Precision@5 can differ from Hit@5. The other questions have one labeled chunk, so for them Recall@5 matches Hit@5 and Precision@5 is Hit@5 divided by 5. Latency is how long that search takes after one warmup query, not the time until the model finishes an answer. `--save` appends that summary to `rag_eval/benchmarks.md`; `--message` is an optional note above it. Without `--save` nothing is written to a file.

`ragas_eval.py` asks the same chat prompt, using whatever `MODE` is set to, then scores the finished answers with RAGAS. The reference for each question is its `evidence` sentence. Run it from `backend` the same way. On this Python, `scikit-network` has no installable build and is only used by RAGAS to synthesize test sets, so install RAGAS itself with `pip install ragas==0.4.3 --no-deps` after the rest of `requirements.txt`.
