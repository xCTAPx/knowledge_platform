# Knowledge Platform

Base project structure for a knowledge platform.

- Backend: FastAPI (Python)
- Frontend: React (JavaScript, Vite)

There is no business logic yet — only the skeleton needed to run both apps.

## Requirements

- Python 3.11+
- Node.js 18+

## Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs  
Health check: http://localhost:8000/api/v1/health

## Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173
