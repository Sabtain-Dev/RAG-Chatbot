import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.rag.embeddings import create_embeddings
from app.rag.vectordb import collection

TEST_QUERIES = [
    # In-Domain Queries (Should have LOW distance)
    "Tell me about Lumeluxe",
    "What is the price of Herbal Hair Oil & Shampoo?",
    "How does Lumeluxe protect my privacy?",
    
    # Out-Of-Domain Queries (Should have HIGH distance)
    "Do you ship products to Mars?",
    "Who won the 2022 FIFA World Cup?",
    "How do I repair a broken smartphone screen?"
]

def calibrate():
    print("=" * 80)
    print(" RETRIEVAL DISTANCE CALIBRATION TOOL")
    print("=" * 80)

    for query in TEST_QUERIES:
        embedding = create_embeddings([query], is_query=True)
        results = collection.query(
            query_embeddings=embedding,
            n_results=3,
            include=["documents", "distances"]
        )

        docs = results["documents"][0] if results["documents"] else []
        distances = results["distances"][0] if results["distances"] else []

        print(f"\n❓ Query: '{query}'")
        if not docs:
            print("    No documents retrieved.")
            continue

        for i, (doc, dist) in enumerate(zip(docs, distances)):
            snippet = doc.replace("\n", " ")[:80] + "..."
            print(f"   Rank {i+1} | Distance: {dist:.4f} | Snippet: {snippet}")

    print("\n" + "=" * 80)
    print("  CALIBRATION RULE:")
    print(" Find the lowest distance among Out-of-Domain queries.")
    print(" Set DISTANCE_THRESHOLD lower than that value in app/chatbot/retriever.py.")
    print("=" * 80)

if __name__ == "__main__":
    calibrate()