# Architecture

This document describes the current implementation of edurag (Reusable RAG API backend for accurate AI assistants in education).

## System Purpose

Provide a retrieval-augmented generation (RAG) HTTP API that any educational institution can use to answer questions based on its own content. The backend uses vector embeddings to ground responses. A specific assistant persona and data source (e.g. scraped pages from one institution) are used as an example.

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Institution["Educational Institution"]
        Content[Content Sources<br/>Website • Documents]
    end

    Content --> Ingest[Ingestion + Embeddings]
    Ingest --> Vector[(Postgres + pgvector)]

    subgraph edurag["edurag"]
        Web[React/TS Chat Widget]
        API[API<br/>/chat]
        RAG[RAG Engine]
    end

    Web --> API

    Vector --> RAG
    API --> RAG
    RAG --> LLM[LLM Provider]

    Clients[Client Platforms] --> API

    subgraph Clients
        Web[Web Widget]
        Mobile[Mobile Apps]
        Dashboard[Chat Dashboards]
        Other[Any Platform]
    end
```

## Component Breakdown

```
┌─────────────────┐       ┌──────────────────────┐
│   HTTP Client   │──────▶│  Flask Application   │
│  (any / web UI) │       │   (app/)             │
└─────────────────┘       └──────────┬───────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                       Request Handling                       │
│  routes.py: /, /chat, /health                                │
│    - extract message + optional session_id                   │
│    - load history from Postgres                              │
│    - call chatbot.chat(...)                                  │
│    - persist user + assistant messages                       │
└─────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Chatbot (chatbot.py)                     │
│  - Global: HuggingFaceEmbeddings + PGVector retriever (k=6) │
│  - Per-thread: ChatGroq (llama-3.3-70b-versatile, t=0.3)    │
│  - SYSTEM_PROMPT with institution persona                    │
│  - Retrieval → context injection → history + question → LLM  │
└─────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
            ┌──────────────┐  ┌──────────┐   ┌─────────────┐
            │   pgvector   │  │  Groq    │   │  Postgres   │
            │ (vector DB)  │  │  (LLM)   │   │ (chat hist) │
            └──────────────┘  └──────────┘   └─────────────┘
                    (same Postgres instance)
```

## Core Modules

| Module         | Responsibility |
|----------------|----------------|
| `app/__init__.py` | Flask application factory. Registers blueprint. Sets CORS and secret key. |
| `app/routes.py`   | Blueprint with `GET /` (landing page + widget), `POST /chat`, and `GET /health`. Calls init_db on every request. Generates session_id if absent. |
| `app/chatbot.py`  | RAG implementation. Module-level retriever and embeddings. Thread-local LLM. System prompt construction and LLM invocation. |
| `app/db.py`       | Postgres wrapper (psycopg2). `messages` table (id, session_id, role, content, created_at). History limited to last 10 messages (reverse chronological on read, restored before LLM). |
| `app/ingest.py`   | Offline data pipeline. Hardcoded list of 18 URLs. Scrapes, strips structural tags, splits (500/50 overlap), embeds, writes to pgvector (collection rebuilt on each run). |
| `frontend/`       | React + TypeScript chat widget source, built with Vite straight into `app/static/widget/`. |
| `run.py`          | Development server launcher. |
| `docker-compose.yml` | `db` (Postgres + pgvector) and `web` (Flask) services. Mounts source for live reload. Uses .env file. |
| `Procfile`        | gunicorn invocation for platform deployments. |

## Data Stores

Both the vector store and conversation history live in one Postgres database (via `DATABASE_URL`), provisioned as the `db` service in `docker-compose.yml` using the `pgvector/pgvector` image.

- **Vector store**: pgvector collection `edurag_docs` (via `langchain-postgres`'s `PGVector`). Contains embeddings + documents + metadata (source URL). Created/rebuilt exclusively by `ingest.py` (`pre_delete_collection=True`).
- **Conversation store**: `messages` table. Per-session message log, indexed on `(session_id, created_at)`. `get_history` returns most recent N rows reversed to chronological order.

## Chat Request Flow (Sequence)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant F as Flask (routes)
    participant D as db.py
    participant B as chatbot.py
    participant R as Retriever (pgvector)
    participant L as LLM (ChatGroq)
    participant S as Postgres

    C->>F: POST /chat {message, session_id?}
    F->>D: init_db()  (idempotent)
    F->>D: get_history(session_id)
    D-->>F: history[] (last 10)
    F->>B: chat(session_id, question, history)

    B->>R: invoke(question)
    R-->>B: docs[6]

    B->>B: build messages:<br/>SystemPrompt(context) + history + Human(question)
    B->>L: invoke(messages)
    L-->>B: response.content

    B-->>F: answer
    F->>S: save_message(session_id, "user", question)
    F->>S: save_message(session_id, "assistant", answer)
    F-->>C: {ok, session_id, message}
```

## Ingestion Pipeline

```mermaid
flowchart TD
    A[ingest.py:main] --> B[for each URL in hardcoded list]
    B --> C[requests.get + BeautifulSoup]
    C --> D[remove script,style,nav,footer,header]
    D --> E[text = soup.get_text separator=\n]
    E --> F[RecursiveCharacterTextSplitter<br/>chunk_size=500, overlap=50]
    F --> G[create_documents with metadata source=URL]
    G --> H[PGVector.from_documents<br/>all-MiniLM-L6-v2 embeddings]
    H --> I[collection=edurag_docs, pre_delete_collection=True]
    I --> J[Process complete]
```

## Retrieval and Prompting

- Embeddings model: `all-MiniLM-L6-v2` (HuggingFaceEmbeddings). Loaded once at import time.
- Retriever: `vectorstore.as_retriever(search_kwargs={"k": 6})`. Global singleton.
- Context construction: `"\n\n".join(d.page_content for d in docs)`
- The system prompt is defined in `app/chatbot.py`. It is an example for an educational institution and should be replaced with institution-specific instructions when adapting the system.

- History messages are converted to HumanMessage / AIMessage.
- New question appended as final HumanMessage.
- No tool calling, agents, or LangGraph nodes are executed at runtime (langgraph is listed in requirements but unused by source).

## Concurrency Model

- Flask run with `threaded=True` (development) and gunicorn (workers + threads) in production.
- Embeddings and pgvector retriever are treated as read-only after module load.
- LLM instances are stored in `threading.local()` because `ChatGroq` is documented as non-thread-safe.
- Postgres connections are opened and closed per operation (no connection pooling).

## Initialization Order (at import / first request)

1. `run.py` imports `create_app`.
2. `app/__init__.py` creates Flask instance and registers blueprint.
3. First request triggers `bp.before_app_request` → `init_db()`.
4. `chatbot.py` top level executes on first import:
   - `load_dotenv()`
   - Instantiates global `embeddings` and `vectorstore` + `retriever`.

## Configuration Surface

All configuration is environment-driven. No config files or command-line flags beyond what Flask/gunicorn accept.

| Name            | Used by          | Default             | Notes |
|-----------------|------------------|---------------------|-------|
| GROQ_API_KEY    | chatbot.py       | (none)              | Required for ChatGroq |
| DATABASE_URL    | db.py, chatbot.py, ingest.py | postgresql://edurag:edurag@localhost:5432/edurag | Postgres + pgvector connection |
| SECRET_KEY      | app/__init__.py  | change-in-prod      | Flask signing |

## Non-Functional Characteristics (Observed)

- No authentication or rate limiting implemented.
- No input sanitization beyond `.strip()` on message.
- Error responses return raw exception strings on 500.
- Ingest is not exposed via HTTP; it is a standalone CLI script.
- Vector store and conversation history live in the same Postgres instance and must be volume-mounted (or externally hosted) for persistence.
- All scraping targets are static in source (no dynamic discovery or sitemap).

## Diagrams Summary

- Component overview (top)
- Sequence for `/chat` (above)
- Ingestion pipeline (above)

Additional runtime view:

```mermaid
flowchart LR
    subgraph "Process"
        Flask
        subgraph "Module Globals"
            Emb[HuggingFaceEmbeddings]
            VS[PGVector Vectorstore]
            Retr[Retriever k=6]
        end
        subgraph "Thread Locals"
            LLM[ChatGroq]
        end
    end

    Flask --> Retr
    Flask --> LLM
    Retr --> VS
    VS --> Emb
```

## Files of Record

All behavior is defined in the Python modules listed under "Core Modules". No external configuration or generated code drives the RAG or persistence logic.
