from pydantic import BaseModel, Field
from typing import Literal


class AskRequest(BaseModel):
    question: str = Field(min_length=1)



class Source(BaseModel):
    chunk_id: str
    email_id: str
    thread_id: str
    gmail_link: str


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
    generation_time: float | None = None

    error: str | None = None