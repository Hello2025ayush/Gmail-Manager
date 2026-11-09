from pydantic import BaseModel, Field
from typing import Literal


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


class SyncRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)


class SyncResponse(BaseModel):
    synced: int
    requested: int
    skipped: int = 0
    failed: int = 0


class SyncStatus(BaseModel):
    active: bool
    phase: str
    processed: int
    total: int | None = None
    synced: int
    skipped: int
    failed: int


class ConnectResponse(BaseModel):
    email: str



class Source(BaseModel):
    chunk_id: str
    email_id: str
    thread_id: str
    gmail_link: str
    subject: str = ""
    date: str = ""
    sender: str = ""


class AskResponse(BaseModel):

    status: Literal[
        "success",
        "insufficient_evidence",
        "invalid_response",
        "llm_error"
    ]

    answer: str | None = None

    citations: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)

    retrieval_time: float | None = None
    context_time: float | None = None
    generation_time: float | None = None
    model_load_time: float | None = None
    prompt_eval_time: float | None = None
    token_gen_time: float | None = None
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    tokens_per_second: float | None = None
    total_time: float | None = None

    error: str | None = None
