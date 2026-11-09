# Gmail Manager

Ask questions about synced Gmail messages with local retrieval and an Ollama model.

## Setup

1. Create a Google OAuth desktop client and put its JSON file at `backend/app/credentials.json`.
2. Copy `.env.example` to `.env` and set `DATABASE_URL` to your PostgreSQL connection string.
3. Install Python packages from `backend/requirement.txt` in your virtual environment.
4. Install and start Ollama, then download the model with `ollama pull qwen2.5:1.5b`.
5. From `backend`, run `uvicorn app.main:app --reload`.
6. From `frontend`, run `python -m http.server 5500` and open `http://localhost:5500`.

Click **Connect Gmail** to complete Google sign-in. Inbox sync shows emails processed, added, skipped, failed, and remaining while it runs. Messages already indexed are skipped on later syncs. The first sync with the BGE embeddings adds the selected emails to a separate Qdrant collection; later syncs skip those indexed messages.

## Retrieval flow

The app uses the free, local [BAAI BGE small English embedding model](https://huggingface.co/BAAI/bge-small-en-v1.5). It searches chunks with Qdrant semantic search and BM25 keyword search, combines the rankings, then reranks candidates with a local cross-encoder. It fetches matching emails from PostgreSQL for the Ollama prompt and returns Gmail links for cited messages.

Set `OLLAMA_MODEL` in `.env` to try another local chat model. For a faster, smaller option, try `qwen2.5:0.5b`; it uses fewer parameters and may give less reliable answers. Run `ollama pull qwen2.5:0.5b` before selecting it.

Sync the latest 1–500 messages from the page. Existing emails remain stored, and later syncs skip messages that already have indexed chunks.
