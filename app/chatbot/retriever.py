from app.rag.embeddings import create_embeddings
from app.rag.vectordb import collection

# Calibrated Distance Threshold:
# Based on empirical tests from scripts/calibrate_retriever.py:
# - Valid Lumeluxe queries: 0.1833 - 0.3676
# - Out-of-Domain queries:  0.4652 - 0.5646
MAX_DISTANCE_THRESHOLD = 0.40


def retrieve(question: str, top_k: int = 3) -> list[str]:
    """Retrieve relevant context chunks from ChromaDB filtered by calibrated L2 distance."""
    # 1. Generate query embedding using BGE query instruction prefix
    embeddings = create_embeddings([question], is_query=True)

    # 2. Query ChromaDB for top_k documents and L2 distances
    results = collection.query(
        query_embeddings=embeddings,
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )

    docs = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []

    if not docs:
        return []

    # 3. Keep chunks strictly within our calibrated 0.40 L2 distance limit
    valid_docs = [
        doc
        for doc, dist in zip(docs, distances)
        if dist <= MAX_DISTANCE_THRESHOLD
    ]

    return valid_docs