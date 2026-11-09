import logging


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import setting
from app.utils.logger import setup_logging

from app.schemas import AskRequest, AskResponse, SyncRequest, SyncResponse, SyncStatus, ConnectResponse
from app.llm import answer_question


setup_logging()

logger = logging.getLogger(__name__)
sync_status = {
    "active": False,
    "phase": "idle",
    "processed": 0,
    "total": None,
    "synced": 0,
    "skipped": 0,
    "failed": 0
}


app = FastAPI(title = setting.APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    logger.info("Root Endpoint called")

    return {
        "message" : "This is Gmail Manager"
    }


@app.get("/health")
def health():
    return {
        "status" : "ok"
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    return answer_question(request.question)


@app.post("/sync", response_model=SyncResponse)
def sync(request: SyncRequest):
    from googleapiclient.errors import HttpError
    from app.database.models import create_table
    from app.database.connection import engine
    from app.gmail.auth import get_gmail_api_object
    from app.gmail.fetcher import list_messages, get_message_content
    from app.ingestion.parser import parse_email
    from app.ingestion.chunker import chunk_email
    from app.database.repository import save_email
    from app.vector_store import create_collection, insert_chunks, email_has_chunks

    sync_status.update({
        "active": True,
        "phase": "connecting",
        "processed": 0,
        "total": None,
        "synced": 0,
        "skipped": 0,
        "failed": 0
    })

    try:
        service = get_gmail_api_object()
        message_ids = list_messages(service, request.limit)
        sync_status.update({"phase": "indexing", "total": len(message_ids)})

        create_table(engine)
        create_collection()

        for index, message in enumerate(message_ids, start=1):
            try:
                if email_has_chunks(message["id"]):
                    sync_status["skipped"] += 1
                    continue

                raw_email = get_message_content(service, message["id"])
                email = parse_email(raw_email)
                save_email(email)
                chunks = chunk_email(email, chunk_size=200, chunk_overlap=40)
                insert_chunks(chunks)
                sync_status["synced"] += 1
            except HttpError as error:
                logger.error("Failed to sync email %s: %s", message.get("id"), error)
                sync_status["failed"] += 1
            finally:
                sync_status["processed"] = index

        return {
            "synced": sync_status["synced"],
            "requested": request.limit,
            "skipped": sync_status["skipped"],
            "failed": sync_status["failed"]
        }
    except Exception:
        sync_status["phase"] = "error"
        raise
    finally:
        sync_status["active"] = False
        if sync_status["phase"] != "error":
            sync_status["phase"] = "complete"


@app.get("/sync/status", response_model=SyncStatus)
def get_sync_status():
    return sync_status


@app.post("/connect", response_model=ConnectResponse)
def connect():
    from app.gmail.auth import get_gmail_api_object

    service = get_gmail_api_object()
    profile = service.users().getProfile(userId="me").execute()
    return {"email": profile["emailAddress"]}
