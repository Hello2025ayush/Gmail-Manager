import logging
from pathlib import Path
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError


from app.config import setting
from app.utils.logger import setup_logging


logger = logging.getLogger(__name__)


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

BASE_DIR = Path(__file__).resolve().parents[1]           



def get_credentials():
    creds = None

    token_path = BASE_DIR / setting.GOOGLE_TOKEN_FILE
    credentials_path = BASE_DIR / setting.GOOGLE_CREDENTIALS_FILE

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)


    if creds and creds.valid:
        return creds


    if creds and creds.expired and creds.refresh_token:
         try:
            creds.refresh(Request())
         except RefreshError:
            creds = None


    if not creds or not creds.valid:
        ## login agaiin
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)


    token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def get_gmail_api_object():
    creds = get_credentials()

    service = build("gmail", "v1", credentials = creds)

    return service



if __name__ == "__main__":
    setup_logging()

    service = get_gmail_api_object()

    request = service.users().labels().list(userId = "me")
    # request = service.users().messages().list(userId = "me", maxResults = 10)

    result = request.execute()

    print(json.dumps(result, indent=4))





