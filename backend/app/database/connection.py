from sqlalchemy import create_engine

from app.config import setting

engine = create_engine(
    setting.DATABASE_URL,
    pool_pre_ping=True
)
