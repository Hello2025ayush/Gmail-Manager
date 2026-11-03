import json
from pathlib import Path
from app.ingestion.embedder import generate_embeddings

from uuid import uuid5, NAMESPACE_URL

from qdrant_client import QdrantClient, models


BASE_DIR = Path(__file__).resolve().parents[1]

client = QdrantClient(
    path=str(BASE_DIR / "qdrant_data")
)

COLLECTION_NAME = "email_chunks"


def create_collection():

    if client.collection_exists(COLLECTION_NAME):
        print("Collection already exists")
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=384,
            distance=models.Distance.COSINE
        )
    )

    print("Collection created successfully!")


# --------------------------------------------------------------- #
def insert_chunks(chunks):

    if not chunks:
        return

    texts = []
    for chunk in chunks:
        texts.append(chunk["text"])

    vectors = generate_embeddings(texts)

    points = []

    for i in range(len(chunks)):
        point = models.PointStruct(
            id=str(uuid5(NAMESPACE_URL, str(chunks[i]["chunk_id"]))),
            vector=vectors[i],
            payload=chunks[i]
        )

        points.append(point)

    client.upsert(                                      #insert
        collection_name=COLLECTION_NAME,
        points=points
    )

    print("Stored", len(points), "chunks in Qdrant")


# --------------------------------------------------------------- #
def search_chunks(question, top_k=5):

    
    vector = generate_embeddings([question])[0]

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=top_k,
        with_payload=True
    ).points

    
    chunks = []

    for result in results:

        chunk = result.payload.copy()
        chunk["score"] = result.score

        chunks.append(chunk)

    # print(json.dumps(chunk, indent = 4))

    return chunks






if __name__ == "__main__":
    create_collection()

    question = "whats the email about Vigilance Awareness Week says"
    
    results = search_chunks(question, top_k=3)

    print("Question:", question)
    print("Results found:", len(results))

    for i, chunk in enumerate(results, start=1):

        print(f"\nResult {i}")
        print("Chunk ID:", chunk["chunk_id"])
        print("Email ID:", chunk["email_id"])
        print("Score:", round(chunk["score"], 4))
        print("Text:", chunk["text"][:300])


    client.close()
    