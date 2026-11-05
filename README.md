# Knowledge Platform

A personal library with a chat over your own notes and files.

You register, keep notes and attachments in one tape, and ask questions in a saved chat. The answer is streamed from an OpenAI-compatible LLM. Before the call, dense search and BM25 each propose twenty chunks. The reranker reads the combined list, and the top five are added to the prompt.

- Backend: FastAPI, PostgreSQL, Qdrant
- Frontend: React, TypeScript, Vite
- Embeddings: `BAAI/bge-m3` on CUDA, then `BAAI/bge-reranker-v2-m3`

## Requirements

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Docker, for Qdrant
- An NVIDIA GPU. The embedder and reranker are loaded on `cuda:0` when the API starts

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

`copy` is the Windows command. On macOS and Linux, use `cp .env.example .env`.

In `.env`, replace `YOUR_PASSWORD` with the password you chose when installing PostgreSQL. That placeholder is not a real password: login fails with `password authentication failed for user "postgres"` until `DATABASE_URL` has the real one. Also set `JWT_SECRET` and `LLM_API_KEY`.

API docs: http://localhost:8000/docs  
Health check: http://localhost:8000/api/v1/health  
Qdrant dashboard: http://localhost:6333/dashboard — collection `chunks`

On startup the API loads the embedding model. If the `chunks` collection is empty, it indexes every existing note and file. After that, a note is reindexed when you save it, and a file is indexed when you upload it. Accepted uploads are PDF, txt, and Markdown, up to 10 MB. Text is split into chunks of 600 tokens with an overlap of 80. Search returns the 5 nearest chunks of the signed-in user.

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

The script calls the same search the chat uses, including BM25 and the reranker. Hit@5 is the share of questions whose labeled chunk appears in the five results. MRR@5 is the average of `1 / rank` for the first labeled chunk, or 0 when it is missing. Latency is how long that search takes after one warmup query, not the time until the model finishes an answer. `--save` appends that summary to `rag_eval/benchmarks.md`; `--message` is an optional note above it. Without `--save` nothing is written to a file.
