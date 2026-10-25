import logging
from app.config import setting

def setup_logging():
    logging.basicConfig(
        level = setting.LOG_LEVEL.upper(),
        format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
