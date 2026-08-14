import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.rag.chunker import load_documents, split_text_smart
from app.rag.embeddings import create_embeddings
from app.rag.vectordb import collection, reset_collection

CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
MIN_DOC_CHARS = 150

PRODUCT_NAME_LINE = re.compile(r"^PRODUCT:\s*(.+)$", re.MULTILINE)
CATEGORY_LINE = re.compile(r"^Category:\s*(.+)$", re.MULTILINE)


def build_metadata(source_name: str, chunk: str, chunk_index: int) -> dict:
    """
    Product chunks get product_name/category metadata so the retriever and
    generator know exactly which product a chunk describes (Day 8 Part 4).
    Non-product chunks get a simpler page-level tag. 'url' is left empty —
    the live site doesn't expose individual product URLs (confirmed earlier:
    it's a client-rendered SPA with no per-product routes), so nothing is
    fabricated here; Day 9's product-page discovery would fill this in.
    """
    if source_name == "products":
        name_match = PRODUCT_NAME_LINE.search(chunk)
        category_match = CATEGORY_LINE.search(chunk)
        return {
            "source": "product",
            "product_name": name_match.group(1).strip() if name_match else "Unknown",
            "category": category_match.group(1).strip() if category_match else "General",
            "url": "",
            "chunk_index": chunk_index,
        }

    return {
        "source": "page",
        "page": source_name,
        "chunk_index": chunk_index,
    }


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

        page_label = source_name.replace("_", " ").title()
        prefixed_chunks = [f"Page: {page_label}\n{c}" for c in chunks]

        embeddings = create_embeddings(prefixed_chunks)

        ids = [f"{source_name}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [build_metadata(source_name, chunks[i], i) for i in range(len(chunks))]

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