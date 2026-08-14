# tests/test_retrieval.py
import json
from pathlib import Path
import pytest
from app.chatbot.retriever import retrieve
from app.rag.vectordb import collection

QUESTIONS_PATH = Path(__file__).parent / "retrieval_questions.json"


def _load_questions():
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# Skips gracefully in CI (or any fresh checkout) where chroma_db hasn't
# been populated by scripts/index_documents.py yet — see Day 9 Step 1.
# Locally, after indexing, this runs for real.
@pytest.mark.skipif(
    collection.count() == 0,
    reason="ChromaDB is empty — run scripts/index_documents.py locally before this test can validate retrieval.",
)
@pytest.mark.parametrize("item", _load_questions())
def test_product_retrieval(item):
    results = retrieve(item["question"], top_k=3)
    assert results, f"No results returned for: {item['question']}"

    combined_text = " ".join(r["document"].lower() for r in results)
    assert item["expected_product"] in combined_text, (
        f"Expected '{item['expected_product']}' in top results for "
        f"'{item['question']}', got: {[r['metadata'].get('product_name') for r in results]}"
    )