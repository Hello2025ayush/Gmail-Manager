import logging


from fastapi import FastAPI
from app.config import setting
from app.utils.logger import setup_logging

from app.schemas import AskRequest, AskResponse
from app.llm import answer_question


setup_logging()

logger = logging.getLogger(__name__)


app = FastAPI(title = setting.APP_NAME)

@app.get("/")
def root():
    logger.info("Root Endpoint called")

    return {
        "message" : "This is Gmail Manager"
    }


@app.get("/health")
def health():
    return {
        "status" : "okkkk"
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    return answer_question(request.question)