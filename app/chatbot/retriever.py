from app.rag.embeddings import create_embeddings
from app.rag.vectordb import collection

# Cosine distance threshold calibrated for BGE / SentenceTransformers:
# Cosine distances typically fall between 0.20 and 0.65 for valid context matches.
MAX_DISTANCE_THRESHOLD = 0.65


def retrieve(question: str, top_k: int = 5) -> list[str]:
    """Retrieve relevant context chunks from ChromaDB filtered by distance."""
    # 1. Generate query embedding using BGE query instruction prefix
    embeddings = create_embeddings([question], is_query=True)

    # 2. Query ChromaDB for top_k documents and distances
    results = collection.query(
        query_embeddings=embeddings,
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )

    docs = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []

    if not docs:
        return []

    # 3. Filter chunks within the calibrated cosine distance threshold
    valid_docs = [
        doc
        for doc, dist in zip(docs, distances)
        if dist <= MAX_DISTANCE_THRESHOLD
    ]

    # Safety fallback: If top result is close enough, return top_k to avoid false fallbacks
    if not valid_docs and distances and distances[0] <= 0.70:
        return docs[:2]

    return valid_docs