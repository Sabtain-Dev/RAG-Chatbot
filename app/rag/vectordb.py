from pathlib import Path
import chromadb

CHROMA_PATH = Path("chroma_db")
client = chromadb.PersistentClient(path=str(CHROMA_PATH))

collection = client.get_or_create_collection(
    name="lumeluxe_knowledge",
    metadata={"hnsw:space": "cosine"},
)


def reset_collection():
    """
    Clears all existing vectors before a full re-index so stale chunks
    from a previous run (different chunk counts per source) don't linger.
    Deletes by ID rather than dropping the collection, so the module-level
    `collection` object stays valid for callers that already imported it.
    """
    existing = collection.get()
    ids = existing.get("ids", [])
    if ids:
        collection.delete(ids=ids)
        print(f" Cleared {len(ids)} existing chunk(s) before reindexing.")
    return collection