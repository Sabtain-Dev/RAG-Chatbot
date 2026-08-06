import re
from pathlib import Path
from typing import List, Dict, Optional

CHUNK_SIZE = 600
CHUNK_OVERLAP = 120
MIN_PARAGRAPH_LEN = 30

# A paragraph that looks like a product card (has a price/rating) stays
# standalone — one product per chunk, for retrieval precision — instead
# of being merged with unrelated neighboring paragraphs.
PRODUCT_INDICATOR = re.compile(r"(rs\.?\s?\d|₨\s?\d|pkr\s?\d|\$\s?\d|[★☆])", re.IGNORECASE)


def load_documents(data_dir: Optional[Path] = None) -> List[Dict[str, str]]:
    """Loads all cleaned text files. Defaults to data/cleaned/ if no dir given."""
    data_path = Path(data_dir) if data_dir else Path("data/cleaned")
    docs = []

    if not data_path.exists():
        print(f" Directory {data_path} does not exist.")
        return docs

    for file in data_path.glob("*.txt"):
        with open(file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                docs.append({"source": file.stem, "text": content})

    return docs


def split_text_smart(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Paragraph-aware chunking:
    - Product-card paragraphs (price/rating present) stay standalone.
    - Other short paragraphs get merged together up to chunk_size, so
      narrative content carries surrounding context instead of being
      embedded as isolated single sentences.
    - Paragraphs longer than chunk_size get sentence-split with overlap.
    """
    if "Source URL:" in text and "=" * 50 in text:
        parts = text.split("=" * 50, 1)
        if len(parts) > 1:
            text = parts[1].strip()

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    buffer = ""

    def flush_buffer():
        nonlocal buffer
        if buffer:
            chunks.append(buffer.strip())
            buffer = ""

    for p in paragraphs:
        if len(p) < MIN_PARAGRAPH_LEN:
            continue

        if len(p) > chunk_size:
            flush_buffer()
            sentences = re.split(r"(?<=[.!?])\s+", p)
            current = ""
            for s in sentences:
                if len(current) + len(s) + 1 > chunk_size and current:
                    chunks.append(current)
                    tail = current[-overlap:] if overlap > 0 else ""
                    current = f"{tail} {s}".strip() if tail else s
                else:
                    current = f"{current} {s}".strip() if current else s
            if current:
                chunks.append(current)
            continue

        if PRODUCT_INDICATOR.search(p):
            flush_buffer()
            chunks.append(p)
            continue

        candidate = f"{buffer} {p}".strip() if buffer else p
        if len(candidate) > chunk_size:
            flush_buffer()
            buffer = p
        else:
            buffer = candidate

    flush_buffer()
    return chunks