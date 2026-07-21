<h1 align="center">EduRAG</h1>
<p align="center">
Reusable Retrieval-Augmented Generation (RAG) backend for educational AI assistants.
</p>
<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/Chroma-Vector_DB-7B61FF?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<br>

![REST API](https://img.shields.io/badge/REST-API-0A66C2?style=flat-square)
![Embeddings](https://img.shields.io/badge/Embeddings-HuggingFace-yellow?style=flat-square)
![SQLite](https://img.shields.io/badge/SQLite-Conversation_History-003B57?style=flat-square&logo=sqlite)
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
- LangChain (langchain-classic, langchain-chroma, langchain-huggingface, langchain-groq, langchain-text-splitters)
- Groq (llama-3.3-70b-versatile)
- Hugging Face sentence-transformers (all-MiniLM-L6-v2) for embeddings
- Chroma vector store (persistent)
- SQLite for conversation history
- BeautifulSoup4 + requests for ingestion

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component diagrams, request flows, and module responsibilities.

## Project Layout

```
edurag/
├── app/
│   ├── __init__.py      # Flask app factory
│   ├── routes.py        # HTTP endpoints
│   ├── chatbot.py       # RAG chat logic + prompt + LLM/retriever
│   ├── db.py            # SQLite session message store
│   ├── ingest.py        # One-shot scraper + vector store builder
│   ├── templates/
│   │   └── index.html   # Empty placeholder
│   └── static/
│       ├── css/style.css
│       └── js/chat.js
├── run.py               # Dev entrypoint
├── docker-compose.yml
├── Procfile
├── requirements.txt
└── README.md
```

## Environment Variables

- `GROQ_API_KEY` (required): Groq API key for LLM calls.
- `SECRET_KEY` (optional): Flask secret key. Defaults to `change-in-prod`.
- `DB_PATH` (optional): Path to SQLite database. Defaults to `conversations.db`.

Place variables in `.env` (loaded by dotenv in chatbot.py). Copy `.env.example` as a starting point.

## Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

`requirements.txt` declares CPU-only PyTorch (via PyTorch CPU index) because only the embedding model uses it. The LLM is served by the Groq API.

Create `.env` with `GROQ_API_KEY`.

Build the knowledge base (required before first use):

```bash
python -m app.ingest
```

Start the server:

```bash
python run.py
```

API available at http://localhost:5000

## Docker

```bash
docker compose up --build
```

Volume mounts:
- Source for live reload
- `chroma_db/` for persisted vectors

## Running the Ingest

The ingest script scrapes pages and builds the vector store in `chroma_db/`. The current list of URLs is an example for one institution. Replace it with pages from the target educational institution (or supply your own documents) before running.

```bash
python -m app.ingest
```

Existing `chroma_db/` is overwritten on run.

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
- History (last 10 messages) is loaded from SQLite for the session and passed to the LLM.
- Both user message and assistant reply are persisted after generation.

### GET /health

```json
{"ok": true, "status": "running"}
```

## Behavior

- Retrieval: Top 6 chunks from Chroma using the question embedding.
- Context is injected into a system prompt.
- The system prompt instructs the model to respond naturally without referencing retrieval or documents.
- LLM temperature fixed at 0.3.
- Per-thread LLM instances to avoid thread-safety issues with ChatGroq under Flask threaded mode.
- Chat history is trimmed to most recent 10 messages per session (chronological order restored before LLM call).
- No streaming. Single-turn response per request.

## Frontend

`app/templates/index.html`, `app/static/css/style.css`, and `app/static/js/chat.js` are empty placeholder files. The delivered API surface is the backend only.

## Deployment Notes

- Procfile targets gunicorn with 2 workers / 4 threads.
- In production set `SECRET_KEY` and ensure `GROQ_API_KEY` is available.
- `chroma_db/` must be persisted across restarts (volume or mounted path).
- `conversations.db` is created on first request if missing.

## License
 - [MIT License](`https://opensource.org/license/mit`).
