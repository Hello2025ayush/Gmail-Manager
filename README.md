# Gmail Manager

Gmail Manager lets you sync recent Gmail messages and ask questions about them. Email content is stored in PostgreSQL, searchable chunks and their vectors are stored locally in Qdrant, and Ollama generates answers on your machine. Answers include links to the source Gmail threads.

## Demo

![Gmail Manager demo screenshot](assets/demo.png)

## What it does

- Connects to Gmail with Google OAuth and read-only access.
- Syncs up the latest messages and skips messages that are already indexed.
- Shows sync progress in the frontend.
- Finds relevant email chunks using keyword and semantic search, then reranks them.
- Uses a local Ollama model to answer questions and returns Gmail citations.

## Architecture

The frontend talks to the FastAPI backend. The backend connects to Gmail during sync, stores full messages in PostgreSQL, and stores searchable chunks in Qdrant. For questions, it retrieves and reranks chunks, loads the related email context, and asks Ollama to draft an answer.

```mermaid
flowchart LR
    UI[Web frontend] <-->|HTTP| API[FastAPI backend]
    API <-->|OAuth and messages| Gmail[Gmail API]
    API --> Ingest[Parse, chunk, embed]
    Ingest --> PG[(PostgreSQL<br/>full emails)]
    Ingest --> Q[(Qdrant<br/>chunks and vectors)]
    API --> Search[Hybrid retrieval<br/>BM25, semantic search, reranker]
    Q --> Search
    Search --> Context[Build email context]
    Context <-->|Load full emails| PG
    Context --> LLM[Ollama]
    LLM --> API
```

## How a question is answered

```mermaid
flowchart LR
    A[Question in chat] --> B[Semantic search in Qdrant]
    A --> C[BM25 keyword search]
    B --> D[Combine and rerank chunks]
    C --> D
    D --> E[Load matching emails from PostgreSQL]
    E --> F[Ollama writes an answer]
    F --> G[Answer and Gmail citations]
```

During sync, Gmail messages are parsed, saved in PostgreSQL, split into overlapping chunks, embedded, and added to Qdrant. During a question, the app combines semantic and BM25 rankings, reranks the candidates with a cross-encoder, and sends relevant email context to Ollama. The API checks the model's cited chunk IDs and returns links to their Gmail threads.

## Technology

| Part | Technology | Use |
| --- | --- | --- |
| Frontend | HTML, CSS, JavaScript | Connect, sync, show progress, and chat |
| Backend API | Python, FastAPI, Pydantic | Gmail sync, search, and question endpoints |
| Gmail access | Gmail API, Google OAuth | Read messages with the `gmail.readonly` scope |
| Email database | PostgreSQL, SQLAlchemy, psycopg | Store full parsed emails and thread IDs |
| Vector search | Qdrant local mode | Store and search embedded email chunks |
| Embeddings | `BAAI/bge-small-en-v1.5`, Sentence Transformers | Turn email chunks and questions into vectors |
| Keyword search | `rank-bm25` | Find matches by words in the question |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Reorder the combined search results |
| Answer generation | Ollama, `qwen2.5:1.5b` by default | Generate answers on the local machine |

The embedding and reranking models are downloaded by Sentence Transformers on first use. The answer model is downloaded through Ollama.

## Project structure

```text
Gmail Manager/
├── backend/
│   ├── app/
│   │   ├── database/       # PostgreSQL tables and email queries
│   │   ├── gmail/          # OAuth and Gmail API access
│   │   ├── ingestion/      # Parse, chunk, and embed messages
│   │   ├── utils/          # Logging setup
│   │   ├── llm.py          # Context building and answer generation
│   │   ├── retrieval.py    # BM25, semantic search, and reranking
│   │   ├── vector_store.py # Local Qdrant collection and search
│   │   ├── config.py       # Environment-based settings
│   │   └── main.py         # FastAPI routes and sync progress
│   └── requirement.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── .env                    # Local settings; do not commit
└── README.md
```

Local OAuth credentials and token are kept at `backend/app/credentials.json` and `backend/app/token.json`. Qdrant creates its local data directory when the app runs. These local files and the benchmark `test/` folder are ignored by Git.

## Setup on Windows

### 1. Prepare the services

- Install PostgreSQL and create a database for this project.
- Install Ollama and start it.
- Create a Google OAuth **Desktop app** client, enable the Gmail API for its Google Cloud project, and save the downloaded client JSON as `backend/app/credentials.json`.

The app requests only Gmail read access. On the first **Connect Gmail** action, a browser window opens for Google sign-in. The resulting token is saved locally for future use.

### 2. Configure the backend

Create a virtual environment and install the Python packages:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirement.txt
```

Create a `.env` file in the project root. Set the connection string for your PostgreSQL database; for example:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/gmail_manager
OLLAMA_MODEL=qwen2.5:1.5b
```

Pull the default answer model:

```powershell
ollama pull qwen2.5:1.5b
```

`OLLAMA_MODEL` can be changed to another model already installed in Ollama.

### 3. Start the backend and frontend

In one terminal, from the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend
```

In a second terminal:

```powershell
py -m http.server 5500 --directory frontend
```

Frontend URL: `http://localhost:5500`.

## Using the app

1. Choose **Connect Gmail** and complete Google sign-in.
2. Enter how many latest messages to sync and choose **Sync emails**.
3. Watch the progress and synced, skipped, and failed counts.
4. Ask a question in chat. The send button stays unavailable while an answer is being generated.
5. Open a citation to view its email thread in Gmail.

Messages already indexed in Qdrant are skipped on later syncs. The full email remains in PostgreSQL so the answer step can load its content when needed.

## API

The backend runs at `http://localhost:8000`. Interactive API documentation is available at <http://localhost:8000/docs> while it is running.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Basic service message |
| `GET` | `/health` | Check that the API is running |
| `POST` | `/connect` | Start or reuse OAuth, then return the connected Gmail address |
| `POST` | `/sync` | Sync messages; JSON body: `{"limit": 100}` (1–500) |
| `GET` | `/sync/status` | Read current progress and synced, skipped, and failed counts |
| `POST` | `/ask` | Ask a question; JSON body: `{"question": "What did ... say?"}` |

The `/ask` response includes `status`, `answer`, `sources`, citation IDs, and timing fields for retrieval, context loading, and Ollama generation. Each source includes its subject, sender, date, and Gmail thread link.

## Benchmark results

The local benchmark used 100 questions based on 100 distinct synced emails. Each question identified an email by its subject, and its expected answer was an exact sentence from that email. All 100 requests completed successfully.

| Measure | Result |
| --- | ---: |
| Successful chatbot responses | 100 / 100 (100%) |
| Accuracy, local LLM judge | 1.94 / 2 (97%) |
| Faithfulness, local LLM judge | 1.94 / 2 (97%) |
| Relevance, local LLM judge | 1.94 / 2 (97%) |
| Citation hit rate | 84% |
| Exact citation rate | 46% |
| Citation precision (average per question) | 0.65 |
| Average search time | 1.217 s |
| Average email context time | 0.003 s |
| Average Ollama time | 11.483 s |
| Average total response time | 12.703 s |

Citation hit means the expected email appeared among the chatbot's citations. Exact citation means the returned email IDs matched the expected email alone. The answer-quality scores come from the same local Ollama model used by the chatbot, so they are useful as an initial check, not independent human evaluation. Citation results are computed directly from email IDs. Review examples before presenting the LLM-judge scores as resume claims.
