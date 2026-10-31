from sqlalchemy import (MetaData, Table, Column, String, Text, DateTime, Integer, ForeignKey, Index, func)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()


## thread table

threads = Table(
    "threads",
    metadata,

    Column("id", String, primary_key = True)
)



## email table

emails = Table(
    "emails",
    metadata,

    Column("id", String, primary_key = True),
    Column("thread_id", String, ForeignKey("threads.id"), nullable = False),

    Column("sender", Text),
    Column("recipient", Text),
    Column("cc", Text),
    Column("subject", Text),
    Column("date", Text),
    Column("internal_date", DateTime(timezone=True)),
    Column("body", Text),

    Column("labels", JSONB),
    Column("attachment_filenames", JSONB)
)

## sync table

sync_state = Table(
    "sync_state",
    metadata,

    Column("id", Integer, primary_key = True),
    Column("last_page_token", Text),
    Column("updated_at", DateTime(timezone=True), server_default=func.now())
)



## Indexing

Index("idx_emails_sender", emails.c.sender)
Index("idx_emails_date", emails.c.internal_date)
Index("idx_emails_thread", emails.c.thread_id)


def create_table(engine):
    metadata.create_all(engine)



if __name__ == "__main__":
    import logging
    from app.database.connection import engine
    from app.utils.logger import setup_logging

    setup_logging()
    
    logger = logging.getLogger(__name__)

    create_table(engine)

    logger.info("Database tables is successfully created")

