from app.rag.embeddings import create_embeddings
from app.rag.vectordb import collection

SIMILARITY_THRESHOLD = 0.45  # Minimum similarity score required to accept context

def retrieve(question: str, top_k: int = 3):
    # 1. Generate query embedding with BGE query instruction prefix
    embeddings = create_embeddings([question], is_query=True)

    # 2. Query ChromaDB
    results = collection.query(
        query_embeddings=embeddings,
        n_results=top_k,
        include=["documents", "distances", "metadatas"]
    )

    docs = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []

    if not docs:
        return []

    # 3. Filter retrieved documents by similarity threshold
    valid_docs = []
    for doc, dist in zip(docs, distances):
        similarity = 1.0 - dist
        if similarity >= SIMILARITY_THRESHOLD:
            valid_docs.append(doc)

    return valid_docs