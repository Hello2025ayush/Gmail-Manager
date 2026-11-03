import json
from app.ingestion.embedder import model

tokenizer = model.tokenizer


def chunk_email(email, chunk_size, chunk_overlap):   ## a list of dictionary
    
    max_tokens = model.max_seq_length - tokenizer.num_special_tokens_to_add(pair = False)
    
    text = email["body"]

    tokens = tokenizer.encode(text, add_special_tokens = False)

    chunks = []

    steps = chunk_size - chunk_overlap

    for i in range(0, len(tokens), steps):
        part = tokens[i : i + chunk_size]
        chunk = {
            "chunk_id" : f"{email['id']}_{len(chunks)}",
            "email_id" : email['id'],
            "thread_id" : email["thread_id"],
            "chunk_id" : len(chunks),
            "text" : tokenizer.decode(
                part,
                skip_special_tokens = True,
                clean_up_tokenization_spaces = True
                )           # list
        }

        chunks.append(chunk)

        if(i + chunk_size >= len(tokens)): 
            break


    return chunks
            

if __name__ == "__main__":
    from app.database.repository import get_email

    email = get_email("some_email_id")

    if email:
        chunks = chunk_email(email, chunk_size=200, chunk_overlap=50)

        for c in chunks:
            print(json.dumps(c, indent = 4))