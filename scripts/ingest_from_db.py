# scripts/ingest_from_db.py
import os
import re
import unicodedata
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

CATEGORY_RULES = [
    (re.compile(r"soap", re.IGNORECASE), "Herbal Soap"),
    (re.compile(r"shampoo|hair oil|\bhair\b", re.IGNORECASE), "Haircare"),
    (re.compile(r"serum|cream|lotion|moistur", re.IGNORECASE), "Skincare"),
    (re.compile(r"bundle|gala", re.IGNORECASE), "Bundle"),
]


def infer_category(name: str) -> str:
    for pattern, label in CATEGORY_RULES:
        if pattern.search(name):
            return label
    return "General"


def normalize_unicode(text: str) -> str:
    """Same fix as before — DB itself stores stylized Unicode titles, confirmed
    by the real sample document ('𝙒𝙝𝙞𝙩𝙚𝙣𝙞𝙣𝙜 𝙃𝙚𝙧𝙗𝙖𝙡 𝙎𝙤𝙖𝙥')."""
    return unicodedata.normalize("NFKC", text)


def extract_english_description(raw_description: str) -> str:
    """
    Descriptions are bilingual (Urdu paragraph, then English paragraph, same
    field). The embedding model is English-focused, so mixing scripts in one
    chunk dilutes the embedding signal. Split on paragraph breaks and keep
    only paragraphs containing enough Latin-script characters to be English —
    Urdu paragraphs use Arabic-script Unicode, which this filters out cleanly
    without needing a language-detection library.
    """
    paragraphs = [p.strip() for p in raw_description.replace("\r\n", "\n").split("\n") if p.strip()]
    english_paragraphs = []
    for p in paragraphs:
        latin_chars = len(re.findall(r"[A-Za-z]", p))
        if latin_chars > len(p) * 0.3:  # mostly-Latin-script line
            english_paragraphs.append(p)
    return " ".join(english_paragraphs) if english_paragraphs else raw_description


def build_product_entry(doc: dict) -> str:
    name = normalize_unicode(doc["title"]).strip()
    description = extract_english_description(normalize_unicode(doc.get("description", "")))

    price = doc.get("finalPrice", doc.get("price"))
    original_price = doc.get("price")
    stock = doc.get("stock", 0)
    availability = "In Stock" if stock > 0 else "Out of Stock"
    category = infer_category(name)

    lines = [
        f"PRODUCT: {name}",
        f"Price: Rs.{price}",
    ]
    if original_price and original_price != price:
        lines.append(f"Original Price: Rs.{original_price}")
    lines.append(f"Availability: {availability}")
    lines.append(f"Category: {category}")

    tags = []
    if doc.get("trending"):
        tags.append("Trending")
    if doc.get("NewArrival"):
        tags.append("New Arrival")
    if doc.get("limitedStock"):
        tags.append("Limited Stock")
    if tags:
        lines.append(f"Tags: {', '.join(tags)}")

    if description:
        lines.append(f"\nDescription:\n{description}")

    return "\n".join(lines)


def main():
    client = MongoClient(os.environ["MONGO_URI"])
    db = client["Lume_Luxe"]

    # Only sellerproducts, only isActive — orders/users/commissiontransactions
    # are never read here; they contain customer PII and don't belong in a
    # public-facing chatbot's knowledge base.
    products = list(db["sellerproducts"].find({"isActive": True}))
    print(f"Found {len(products)} active product(s) in the database.")

    entries = [build_product_entry(doc) for doc in products]

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CLEANED_DIR / "products.txt"
    header = "Source URL: internal://mongodb/sellerproducts\n" + "=" * 50 + "\n\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + "\n\n".join(entries))

    print(f"Wrote {len(entries)} product entries -> {out_path}")


if __name__ == "__main__":
    main()