from app.rag.embeddings import create_embeddings
from app.rag.vectordb import collection

MAX_DISTANCE_THRESHOLD = 0.65


def retrieve(question: str, top_k: int = 5) -> list[dict]:
    """
    Retrieve relevant chunks from ChromaDB, filtered by distance. Each
    result is {"document": str, "distance": float, "metadata": dict} so
    callers can tell a product chunk from a general page chunk (Day 8 Part 8).
    """
    embeddings = create_embeddings([question], is_query=True)

    results = collection.query(
        query_embeddings=embeddings,
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )

    docs = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []
    metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)

    if not docs:
        return []

    combined = list(zip(docs, distances, metadatas))

    valid = [
        {"document": doc, "distance": dist, "metadata": meta}
        for doc, dist, meta in combined
        if dist <= MAX_DISTANCE_THRESHOLD
    ]

    if not valid and distances and distances[0] <= 0.70:
        return [
            {"document": doc, "distance": dist, "metadata": meta}
            for doc, dist, meta in combined[:2]
        ]

    return valid