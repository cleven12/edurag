<h1 align="center">EduRAG</h1>
<p align="center">
Reusable Retrieval-Augmented Generation (RAG) backend for educational AI assistants.
</p>
<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge)
![pgvector](https://img.shields.io/badge/Postgres-pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<br>

![REST API](https://img.shields.io/badge/REST-API-0A66C2?style=flat-square)
![Embeddings](https://img.shields.io/badge/Embeddings-HuggingFace-yellow?style=flat-square)
![Postgres](https://img.shields.io/badge/Postgres-Conversation_History-336791?style=flat-square&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![Education](https://img.shields.io/badge/Built_for-Education-blueviolet?style=flat-square)
![AI](https://img.shields.io/badge/AI-RAG-success?style=flat-square)
![GitHub stars](https://img.shields.io/github/stars/cleven12/edurag?style=for-the-badge)
![GitHub forks](https://img.shields.io/github/forks/cleven12/edurag?style=for-the-badge)
![GitHub issues](https://img.shields.io/github/issues/cleven12/edurag?style=for-the-badge)
![GitHub last commit](https://img.shields.io/github/last-commit/cleven12/edurag?style=for-the-badge)

</p>

## High-Level Flow

```mermaid
flowchart LR
    Institution[Institution's Content] --> edurag[edurag<br/>RAG + Vector Embeddings]
    edurag --> Platforms[Mobile Apps • Web Widgets<br/>Chat Dashboards • Other Platforms]
```

## Stack

- Python 3 + Flask
- LangChain (langchain-classic, langchain-postgres, langchain-huggingface, langchain-groq, langchain-text-splitters)
- Groq (free-tier, open-source models — currently llama-3.3-70b-versatile)
- Hugging Face sentence-transformers (all-MiniLM-L6-v2) for embeddings
- Postgres + pgvector for the vector store *and* conversation history (one database, via docker-compose)
- BeautifulSoup4 + requests for ingestion
- React + TypeScript chat widget (`frontend/`), built to a static bundle served by Flask

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component diagrams, request flows, and module responsibilities.

## Project Layout

```
edurag/
├── app/
│   ├── __init__.py      # Flask app factory
│   ├── routes.py        # HTTP endpoints (/, /chat, /health)
│   ├── chatbot.py       # RAG chat logic + prompt + LLM/retriever (pgvector)
│   ├── db.py            # Postgres conversation history store
│   ├── ingest.py        # One-shot scraper + pgvector store builder
│   ├── templates/
│   │   └── index.html   # Landing page + chat widget mount point
│   └── static/
│       └── widget/      # Built React/TS widget bundle (generated, gitignored)
├── frontend/            # React + TypeScript chat widget source
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── run.py               # Dev entrypoint
├── docker-compose.yml
├── Procfile
├── requirements.txt
└── README.md
```

## Environment Variables

- `GROQ_API_KEY` (required): Groq API key for LLM calls.
- `DATABASE_URL` (optional): Postgres connection string. Defaults to `postgresql://edurag:edurag@localhost:5432/edurag` (matches the `db` service in `docker-compose.yml`).
- `SECRET_KEY` (optional): Flask secret key. Defaults to `change-in-prod`.

Place variables in `.env` (loaded by dotenv in chatbot.py). Copy `.env.example` as a starting point.

## Local Development

Start Postgres with pgvector (or point `DATABASE_URL` at your own instance):

```bash
docker compose up -d db
```

Install backend dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` declares CPU-only PyTorch (via PyTorch CPU index) because only the embedding model uses it. The LLM is served by the Groq API.

Create `.env` with `GROQ_API_KEY` (and `DATABASE_URL` if it differs from the default).

Build the knowledge base (required before first use):

```bash
python -m app.ingest
```

Build the chat widget (only needed once, or after editing `frontend/`):

```bash
cd frontend && npm install && npm run build
```

Start the server:

```bash
python run.py
```

App available at http://localhost:5000 (landing page + chat widget), API at `/chat`.

For iterating on the widget UI itself, `npm run dev` inside `frontend/` runs a hot-reloading dev server against `/chat` on the same host.

## Docker

```bash
docker compose up --build
```

This starts both the `db` (Postgres + pgvector) and `web` (Flask) services. Volume mounts:
- Source for live reload
- `pgdata` volume for persisted vectors + conversation history

## Running the Ingest

The ingest script scrapes pages and builds the vector store in Postgres (pgvector). The current list of URLs is an example for one institution. Replace it with pages from the target educational institution (or supply your own documents) before running.

```bash
python -m app.ingest
```

The target pgvector collection is dropped and rebuilt on each run.

## Using with your institution

edurag is designed to be adapted. To use for a different educational institution:

- Update the URL list in `app/ingest.py` (or replace the scraping logic with your own content loader).
- Edit the system prompt in `app/chatbot.py` to set the correct name, tone, and contact details for the institution.
- Re-run the ingest script to build a fresh vector store.

The resulting `/chat` endpoint can then be called from any client: mobile applications, web widgets, chat dashboards, or other platforms that need reliable AI assistance.

## API

### POST /chat

Request:

```json
{
  "message": "What programs are offered?",
  "session_id": "optional-uuid"
}
```

Response:

```json
{
  "ok": true,
  "session_id": "uuid",
  "message": {
    "role": "assistant",
    "content": "..."
  }
}
```

- If no `session_id`, a new UUID is generated.
- History (last 10 messages) is loaded from Postgres for the session and passed to the LLM.
- Both user message and assistant reply are persisted after generation.

### GET /health

```json
{"ok": true, "status": "running"}
```

## Behavior

- Retrieval: Top 6 chunks from pgvector using the question embedding.
- Context is injected into a system prompt.
- The system prompt instructs the model to respond naturally without referencing retrieval or documents.
- LLM temperature fixed at 0.3.
- Per-thread LLM instances to avoid thread-safety issues with ChatGroq under Flask threaded mode.
- Chat history is trimmed to most recent 10 messages per session (chronological order restored before LLM call).
- No streaming. Single-turn response per request.

## Frontend

`app/templates/index.html` is a sample institution landing page with a chat widget mounted at `#edurag-chat-root`. The widget itself is a small React + TypeScript app in `frontend/`, built with Vite straight into `app/static/widget/` (`widget.js` / `widget.css`) and served by Flask like any other static asset — no separate frontend server needed in production.

## Deployment Notes

- Procfile targets gunicorn with 2 workers / 4 threads.
- In production set `SECRET_KEY` and ensure `GROQ_API_KEY` and `DATABASE_URL` are available.
- Run `cd frontend && npm install && npm run build` as part of your build step so `app/static/widget/` exists before deploying.
- Postgres (with the pgvector extension) must be reachable and persisted across restarts.

## License
 - [MIT License](`https://opensource.org/license/mit`).
