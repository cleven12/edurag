# mw_agent_api

RAG-based conversational API for Mwenge Catholic University (MWECAU).

Mweca is the assistant implementation. It answers questions about the university using retrieved content from the official website.

## Stack

- Python 3 + Flask

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component diagrams, request flows, and module responsibilities.
- LangChain (langchain-classic, langchain-chroma, langchain-huggingface, langchain-groq, langchain-text-splitters)
- Groq (llama-3.3-70b-versatile)
- Hugging Face sentence-transformers (all-MiniLM-L6-v2) for embeddings
- Chroma vector store (persistent)
- SQLite for conversation history
- BeautifulSoup4 + requests for ingestion

## Project Layout

```
mw_agent_api/
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

The ingest script scrapes a hardcoded list of pages and (re)builds `chroma_db/`.

```bash
python -m app.ingest
```

Existing `chroma_db/` is overwritten on run.

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
- Context is injected into a fixed system prompt.
- The system prompt instructs the model (named Mweca) to respond naturally without referencing retrieval or documents.
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

No license file present in repository.
