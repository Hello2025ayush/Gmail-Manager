from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from app.vector_store import search_chunks, client, COLLECTION_NAME


RERANKER_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
reranker = None


def get_all_chunks():
    chunks = []
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=500,
            offset=offset,
            with_payload=True
        )

        for point in points:
            chunks.append(point.payload)

        if offset is None:
            break

    return chunks


def search_hybrid(question, limit=5):
    if not client.collection_exists(COLLECTION_NAME):
        return []

    all_chunks = get_all_chunks()
    if not all_chunks:
        return []

    corpus = [
        f"{chunk.get('subject', '')} {chunk.get('sender', '')} {chunk['text']}".lower().split()
        for chunk in all_chunks
    ]
    bm25 = BM25Okapi(corpus)
    lexical_scores = bm25.get_scores(question.lower().split())
    lexical = sorted(
        range(len(all_chunks)),
        key=lambda index: lexical_scores[index],
        reverse=True
    )[:10]

    semantic = search_chunks(question, top_k=10)
    by_id = {chunk["chunk_id"]: chunk for chunk in all_chunks}
    ranks = {}

    for rank, chunk in enumerate(semantic, start=1):
        chunk_id = chunk["chunk_id"]
        by_id[chunk_id] = chunk
        ranks[chunk_id] = ranks.get(chunk_id, 0) + 1 / (60 + rank)

    for rank, index in enumerate(lexical, start=1):
        chunk_id = all_chunks[index]["chunk_id"]
        ranks[chunk_id] = ranks.get(chunk_id, 0) + 1 / (60 + rank)

    candidates = [by_id[chunk_id] for chunk_id in ranks]
    pairs = [
        [
            question,
            f"Subject: {chunk.get('subject', '')}\n"
            f"From: {chunk.get('sender', '')}\n"
            f"{chunk['text']}"
        ]
        for chunk in candidates
    ]

    global reranker
    if reranker is None:
        reranker = CrossEncoder(RERANKER_NAME)

    scores = reranker.predict(pairs)
    for index, chunk in enumerate(candidates):
        chunk["score"] = float(scores[index])

    return sorted(candidates, key=lambda chunk: chunk["score"], reverse=True)[:limit]
