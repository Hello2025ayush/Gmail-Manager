import base64
import logging
import json

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def decode_data(data: str) -> str:
    
    if not data:
        return ""

    data += ("=" * ((4 - (len(data) % 4)) % 4))

    decoded_bytes = base64.urlsafe_b64decode(data)

    decoded_str = decoded_bytes.decode("utf-8", errors="replace")

    return decoded_str



def extract_content(payload):         #returns body(str), filenames(list)

    mimetype = payload.get("mimeType", "")
    filename = payload.get("filename")

    ## if its an attachment
    if filename: 
        return "", [filename]


    ## there are multiple subPayloads
    if mimetype.startswith("multipart/"):
        bodies = []                             # a tuple (mimeType, text or content)                        
        attachment = []

        for it in payload.get("parts", []):
            body, files = extract_content(it)

            if body:
                bodies.append((it.get("mimeType", ""), body))

            attachment.extend(files)


        ## contains diff reperesentation of same content
        if mimetype.startswith("multipart/alternative"):
            
            for part_type, body in bodies:
                if part_type == "text/plain":
                    return body, attachment

            
            if bodies:
                return bodies[0][1], attachment

            return "", attachment

        text = ""
        for (mime, content) in bodies:
            if content:
                content += "\n\n"
                text += content
            

        return text, attachment


    ## simple body no multiple parts
    data = payload.get("body", {}).get("data", "")
    text = decode_data(data)

    if mimetype == "text/html":
        soup = BeautifulSoup(text, "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

    elif mimetype != "text/plain":
        text = ""

    return text.strip(), []



def parse_email(message):
    payload = message.get("payload", {})

    header_in_payload = payload.get("headers", [])

    header = {}

    for x in header_in_payload:
        header[x.get("name").lower()] = x.get("value")


    body, file_name = extract_content(payload)

    final = {
        "id"                : message.get("id", ""),
        "threadId"          : message.get("threadId", ""),
        "from"              : header.get("from", ""),
        "to"                : header.get("to", ""),
        "cc"                : header.get("cc", ""),
        "subject"           : header.get("subject", ""),
        "date"              : header.get("date", ""),

        "internalDate"      : message.get("internalDate", ""),
        "body"              : body,
        "labelIds"          : message.get("labelIds", []),
        "attachment_filenames" : file_name
    }

    return final


if __name__ == "__main__":
    from app.gmail.fetcher import get_all_message_content
    from app.gmail.auth import get_gmail_api_object


    gmailObject = get_gmail_api_object()
    message = get_all_message_content(gmailObject, 5)
    
    for mssg in message:
        final = parse_email(mssg)
        print(json.dumps(final, indent = 4))

