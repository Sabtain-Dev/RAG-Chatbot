import sys
from pathlib import Path

# Add project root directory to path for clean imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.rag.embeddings import create_embeddings
from app.rag.vectordb import collection


def search_knowledge_base(query_text: str, top_k: int = 3):
    print(f"\n Querying: '{query_text}'")

    # Embed search query with BGE query instruction enabled
    query_vector = create_embeddings([query_text], is_query=True)[0]

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not docs:
        print(" No relevant chunks found.")
        return

    print("\n" + "=" * 60)
    for idx, (doc, meta, dist) in enumerate(zip(docs, metas, distances), start=1):
        # Convert cosine distance to cosine similarity score
        similarity = round(1 - dist, 4)
        print(f" Rank {idx} | Source: {meta['source']} | Similarity: {similarity}")
        print("-" * 60)
        print(f"{doc.strip()}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    while True:
        try:
            user_query = input("Ask a question about Lumeluxe (or type 'exit'): ").strip()
            if not user_query or user_query.lower() == "exit":
                break
            search_knowledge_base(user_query)
        except (KeyboardInterrupt, EOFError):
            break