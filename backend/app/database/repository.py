from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.database.connection import engine
from app.database.models import emails, threads
from app.gmail.fetcher import get_all_message_content


def save_email(email):

    
    timestamp = email.get("internalDate")

    internal_date = None
    if timestamp:
        internal_date = datetime.fromtimestamp(
            int(timestamp) / 1000,
            tz=timezone.utc
        )

    with engine.begin() as conn:

        
        query = insert(threads).values(
            id=email["threadId"]
        ).on_conflict_do_nothing()

        conn.execute(query)

        
        data = {
            "id": email["id"],
            "thread_id": email["threadId"],
            "sender": email["from"],
            "recipient": email["to"],
            "cc": email["cc"],
            "subject": email["subject"],
            "date": email["date"],
            "internal_date": internal_date,
            "body": email["body"],
            "labels": email["labelIds"],
            "attachment_filenames": email["attachment_filenames"]
        }

        
        query = insert(emails).values(data).on_conflict_do_nothing()

        result = conn.execute(query)

        return result.rowcount == 1


def get_email(email_id):

    query = select(emails).where(emails.c.id == email_id)

    with engine.connect() as conn:
        result = conn.execute(query).mappings().first()

    if result is None:
        return None

    return dict(result)



if __name__ == "__main__":

    from app.gmail.auth import get_gmail_api_object
    from app.ingestion.parser import parse_email
    from app.database.models import create_table
    from app.utils.logger import setup_logging
    import logging

    setup_logging() 
    logger = logging.getLogger(__name__)

    create_table(engine)

    service = get_gmail_api_object()

    raw_emails = get_all_message_content(service, 5)

    inserted = 0
    skipped = 0

    for raw_email in raw_emails:

        parsed = parse_email(raw_email)
        save_email(parsed)

    

    logger.info('successfully inserted all mails into database')