import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.rag.chunker import load_documents, split_text_smart
from app.rag.embeddings import create_embeddings
from app.rag.vectordb import collection, reset_collection

CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

# Skips utility/auth pages (login, register, dashboard) that slipped past
# scrape.py's exclusion filters and produced near-empty cleaned content.
MIN_DOC_CHARS = 150


def index_knowledge_base():
    if not CLEANED_DIR.exists() or not list(CLEANED_DIR.glob("*.txt")):
        print(f" No cleaned text files found in {CLEANED_DIR.relative_to(PROJECT_ROOT)}.")
        print(" Please run 'python scripts/clean_data.py' first!")
        return

    documents = load_documents(CLEANED_DIR)
    if not documents:
        print(" No documents loaded for indexing.")
        return

    print(f" Loaded {len(documents)} cleaned document(s) for indexing.\n")

    reset_collection()
    total_chunks = 0

    for doc in documents:
        source_name = doc["source"]
        raw_text = doc["text"]

        if len(raw_text) < MIN_DOC_CHARS:
            print(f" Skipped '{source_name}' — cleaned content too short ({len(raw_text)} chars).")
            continue

        chunks = split_text_smart(raw_text)
        if not chunks:
            print(f" Skipped '{source_name}' — 0 chunks generated after cleaning.")
            continue

        print(f" Indexing '{source_name}': generated {len(chunks)} chunk(s).")

        # Context-prefix anchors the embedding to the page topic — this is
        # what keeps generic queries from mis-ranking toward unrelated pages.
        page_label = source_name.replace("_", " ").title()
        prefixed_chunks = [f"Page: {page_label}\n{c}" for c in chunks]

        embeddings = create_embeddings(prefixed_chunks)

        ids = [f"{source_name}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]

        collection.upsert(
            ids=ids,
            documents=prefixed_chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )

        total_chunks += len(chunks)

    print(f"\n Indexing Complete! Successfully indexed {total_chunks} chunks into ChromaDB.")


if __name__ == "__main__":
    index_knowledge_base()