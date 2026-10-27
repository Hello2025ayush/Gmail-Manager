import json
import logging
import random 
import time

from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)



def execute_with_retry(request, max_retry = 10):      #returns a dictionary 

    for attempt in range(max_retry + 1):
        try:
            return request.execute()
        
        except HttpError as err:
            status_code = err.resp.status

            reason = ""

            try:
                data = json.loads(err.content)
                # reason = data.get("error", {}).get("errors", [])[0].get("reason")
                errors = data.get("error", {}).get("errors", [])
                
                if errors:
                    reason = errors[0].get("reason")

            except (ValueError, TypeError):
                pass   

            codes = [429, 500, 502, 503, 504]
            possible_reasons = [
                "rateLimitExceeded",
                "userRateLimitExceeded"
            ]

            retryable = (status_code in codes) or (status_code == 403 and reason in possible_reasons)

            if (not retryable) or (attempt == max_retry):
                raise

            # we can retry now
            delay = min(2 ** attempt, 32) + random.uniform(0, 1)

            logger.warning(
                "Gmail API Error %s (%s). Retrying in %.2f seconds",
                status_code,
                reason,
                delay
            )

            time.sleep(delay)



def list_messages(gmailObject, limit = 20):          #returns list of dictionary each having threadID/MailID
    if limit <= 0:
        raise ValueError("Limit should be positive")


    messages = []
    page_token = None

    while len(messages) < limit:
        remaining = limit - len(messages)
        toSend = min(remaining, 500)

        request = gmailObject.users().messages().list(
            userId = "me",
            maxResults = toSend,
            pageToken = page_token
        )

        responce = execute_with_retry(request, 10)

        mssg = responce.get("messages", [])
        for i in mssg:
            messages.append(i)

        page_token = responce.get("nextPageToken")

        logger.info(
            "Fetched %s messages id's successfully!",
            len(messages)
        )

        if page_token == None:
            break


    return messages



def get_message_content(gmailObject, message_id):    #gets content by mssg_id, returns a dict with all details
    
    request = gmailObject.users().messages().get(
        userId = "me",
        id = message_id,
        format = "full"
    )

    mssg = execute_with_retry(request, 5)

    return mssg



def get_all_message_content(gmailObject, total_email_want):  # returns list of dictionaries
    
    messages = list_messages(gmailObject, total_email_want)

    email = []

    for index, value in enumerate(messages, start = 1):
        mssg_id = value.get("id")
        
        try:
            content = get_message_content(gmailObject, mssg_id)
            email.append(content)

        except HttpError as err:
            logger.error(
                "failed to fetch %s / %s message: %s",
                index,
                total_email_want,
                err
            )


    return email



if __name__ == "__main__":

    from app.utils.logger import setup_logging
    from app.gmail.auth import get_gmail_api_object

    setup_logging()
    gmailObject = get_gmail_api_object()

    emails = get_all_message_content(gmailObject, 500)

    print(f"\n successfully fetched emails = {len(emails)} \n")

    print(len(emails))
    for x in emails:
        print(x.get("id"))