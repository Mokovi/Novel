# AI_Novel

Local human-AI collaborative novel writing system.

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000/docs for the interactive API documentation.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 for the Vite dev server.

### Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

## Project Structure

See [docs/design.md](docs/design.md) for the full architecture document.
See [docs/task_moc.md](docs/task_moc.md) for the phased task breakdown.
