# scripts/clean_data.py
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

BOILERPLATE_MIN_FILES = 3
# A line appearing on this fraction (or more) of all pages is always
# treated as site-wide chrome, even if it happens to sit near a price
# line on some short page — fixes taglines like "Lume Luxe FAST DELIVERY
# New Arrival" leaking through the product-context protection window.
STRONG_BOILERPLATE_RATIO = 0.5

MIN_LINE_LEN = 2
SHORT_LINE_MAX = 60
BUFFER_CHAR_LIMIT = 220

# How many lines around a detected price/rating to protect from boilerplate
# stripping — covers card layouts like Name / badge / Price / Rating,
# where the name isn't directly adjacent to the price line.
PRODUCT_CONTEXT_WINDOW = 3
MAX_PRODUCT_PARAGRAPH_LEN = 220
MAX_NAME_WORDS = 8

STAR_RATING_LINE = re.compile(r"^[★☆]+$")
STAR_RATING_ANY = re.compile(r"[★☆]+")

CATEGORY_RULES = [
    (re.compile(r"soap", re.IGNORECASE), "Herbal Soap"),
    (re.compile(r"shampoo|hair oil|\bhair\b", re.IGNORECASE), "Haircare"),
    (re.compile(r"serum|cream|lotion|moistur", re.IGNORECASE), "Skincare"),
    (re.compile(r"bundle|gala", re.IGNORECASE), "Bundle"),
]


def infer_category(name: str) -> str:
    """Lightweight keyword-based categorization — good enough until Day 9's
    proper product-page ingestion can pull real category data from the site."""
    for pattern, label in CATEGORY_RULES:
        if pattern.search(name):
            return label
    return "General"

# Requires an actual digit right after the currency symbol. An earlier
# version used `[\d,]+` which matched a bare comma with no digit at all —
# that's what turned "...content, offers," into a fake "Rs," price hit.
PRICE_TOKEN = re.compile(r"(?:rs\.?\s?|₨\s?|pkr\s?|\$\s?)\d[\d,]*(?:\.\d+)?", re.IGNORECASE)

STOCK_PATTERN = re.compile(r"\b(in stock|out of stock|sold out)\b", re.IGNORECASE)
BADGE_PREFIX = re.compile(r"^(save\s+rs\.?\s?[\d,\.]+\s*)?(new!?\s*)?", re.IGNORECASE)
SENTENCE_END = re.compile(r"[.!?]")
STRAY_CTA_WORDS = re.compile(r"\b(add to cart|view all|save)\b", re.IGNORECASE)

# Phrases that indicate the extracted "name" is actually leftover marketing
# copy, not a real product title. If any of these appear in the name, the
# whole entry is discarded rather than kept with a garbage name — a missing
# product is better than a wrong-looking one in the catalog.
MARKETING_NAME_MARKERS = [
    "special discount", "limited stock", "view all", "meet our",
    "most-wanted", "most wanted", "bestseller", "exclusive gala",
    "trending and new", "new & trending", "new and trending",
    "discover what", "supportive community", "add to cart",
    "save rs", "your destination", "welcome to",
]

NOISE_PATTERNS = [
    r"^\s*0\s*$",
    r"^\s*login\s*$",
    r"^\s*sign in\s*$",
    r"^\s*my account\s*$",
    r"^\s*cart\s*\(?\d*\)?\s*$",
    r"^\s*wishlist\s*$",
    r"^\s*compare\s*$",
    r"^\s*quick view\s*$",
    r"^\s*add to cart\s*$",
    r"^\s*view all\s*$",
    r"^\s*special discounts\.?\s*$",
    r"^\s*limited stocks\s*$",
    r"^\s*meet our most-wanted products\s*$",
    r"^\s*discover what.?s new and most wanted right now!?\s*$",
    r"^\s*trending and new arrivals\s*$",
    r"^\s*bestsellers\s*$",
    r"^\s*new\s*(\&|and)\s*trending\s*$",
    r"^\s*exclusive gala bundles\s*$",
    r"^\s*fast delivery\s*$",
    r"^\s*lume luxe\s+fast delivery\s+new arrival\s*$",
    r"copyright\s*©.*",
    r"^\s*©.*",
    r"all rights reserved",
    r"join us on social",
    r"(tiktok|instagram|facebook|twitter|whatsapp|pinterest)\s*:?\s*https?://\S+",
    r"^\s*subscribe\s*$",
    r"^\s*newsletter\s*$",
    r"^\s*shop all\s*$",
    r"^\s*search\s*$",
    r"^\s*menu\s*$",
    r"^\s*home\s*$",
    r"free (shipping|delivery|membership)",
]


def normalize_unicode(text: str) -> str:
    """Converts stylized Unicode (bold/italic product titles) back to plain ASCII."""
    return unicodedata.normalize("NFKC", text)


def is_noise_line(line: str) -> bool:
    line_lower = line.strip().lower()
    if len(line_lower) < MIN_LINE_LEN:
        return True
    return any(re.search(p, line_lower) for p in NOISE_PATTERNS)


def is_price_or_rating_line(line: str) -> bool:
    return bool(PRICE_TOKEN.search(line)) or bool(STAR_RATING_LINE.match(line.strip()))


def compute_protected_indices(lines: list, window: int = PRODUCT_CONTEXT_WINDOW) -> set:
    """Protects a window of lines around every price/rating line — this is
    what a real product card (name, badge, price, rating) looks like, and
    it must survive boilerplate stripping even if the product repeats
    across multiple pages (homepage + new + trending is normal)."""
    protected = set()
    for i, line in enumerate(lines):
        if is_price_or_rating_line(line):
            for j in range(max(0, i - window), min(len(lines), i + window + 1)):
                protected.add(j)
    return protected


def normalize_for_boilerplate(line: str) -> str:
    return re.sub(r"[^\w\s]", "", line.strip().lower()).strip()


def read_body(raw_text: str):
    raw_text = normalize_unicode(raw_text)
    header = ""
    body = raw_text
    if "Source URL:" in raw_text and "=" * 50 in raw_text:
        parts = raw_text.split("=" * 50, 1)
        header = parts[0].strip() + "\n" + ("=" * 50) + "\n\n"
        body = parts[1].strip() if len(parts) > 1 else ""
    return header, body


def build_boilerplate_index(raw_files) -> dict:
    """Returns {normalized_line: file_ratio} for lines appearing on >= BOILERPLATE_MIN_FILES pages."""
    total_files = len(raw_files)
    line_file_count = defaultdict(set)

    for file_path in raw_files:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        _, body = read_body(raw_text)
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        protected = compute_protected_indices(lines)

        for i, line in enumerate(lines):
            if i in protected:
                continue
            norm = normalize_for_boilerplate(line)
            if norm:
                line_file_count[norm].add(file_path.name)

    return {
        key: len(files) / total_files
        for key, files in line_file_count.items()
        if len(files) >= BOILERPLATE_MIN_FILES
    }


def group_paragraphs(lines):
    """Merges runs of short lines (product-card fragments: title/price/rating)
    into single paragraphs, while leaving naturally long prose lines intact."""
    paragraphs = []
    buffer = []

    def flush():
        if buffer:
            paragraphs.append(" ".join(buffer))
            buffer.clear()

    for line in lines:
        if len(line) > SHORT_LINE_MAX:
            flush()
            paragraphs.append(line)
            continue
        buffer.append(line)
        buffer_len = sum(len(b) for b in buffer)
        if STAR_RATING_LINE.match(line) or buffer_len >= BUFFER_CHAR_LIMIT:
            flush()

    flush()
    return paragraphs


def clean_file_content(raw_text: str, boilerplate: dict) -> str:
    header, body = read_body(raw_text)
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    protected = compute_protected_indices(lines)

    kept = []
    prev_norm = None
    for i, line in enumerate(lines):
        if is_noise_line(line):
            continue

        norm = normalize_for_boilerplate(line)
        ratio = boilerplate.get(norm)
        if ratio is not None:
            # Near-universal lines (site taglines/nav) get stripped no matter
            # what — even if they happen to sit near a price on a short page.
            if ratio >= STRONG_BOILERPLATE_RATIO:
                continue
            # Borderline repeats (e.g. a product cross-listed on 3 pages)
            # only get stripped if NOT inside a protected product window.
            if i not in protected:
                continue

        if norm == prev_norm:  # collapse accidental duplicate lines
            continue

        kept.append(line)
        prev_norm = norm

    paragraphs = group_paragraphs(kept)
    return header + "\n\n".join(paragraphs)


def extract_product_entry(paragraph: str):
    text = paragraph.strip()
    if len(text) > MAX_PRODUCT_PARAGRAPH_LEN:
        return None

    for _ in range(2):
        stripped = BADGE_PREFIX.sub("", text, count=1).strip()
        if stripped == text:
            break
        text = stripped

    first_price = PRICE_TOKEN.search(text)
    if not first_price:
        return None

    name = text[:first_price.start()].strip(" -–—:")
    name = STRAY_CTA_WORDS.sub("", name).strip(" -–—:")
    name = re.sub(r"\s{2,}", " ", name)

    if not (3 <= len(name) <= 80):
        return None
    if len(SENTENCE_END.findall(name)) > 1:
        return None
    if len(name.split()) > MAX_NAME_WORDS:
        return None

    name_lower = name.lower()
    if any(marker in name_lower for marker in MARKETING_NAME_MARKERS):
        return None

    prices = PRICE_TOKEN.findall(text)
    stock_match = STOCK_PATTERN.search(text)
    rating_match = STAR_RATING_ANY.search(text)
    category = infer_category(name)

    lines_out = [f"PRODUCT: {name}", f"Price: {prices[0].strip()}"]
    if len(prices) > 1:
        lines_out.append(f"Original Price: {prices[1].strip()}")
    if stock_match:
        lines_out.append(f"Availability: {stock_match.group(1).title()}")
    if rating_match:
        lines_out.append(f"Rating: {rating_match.group(0)}")
    lines_out.append(f"Category: {category}")

    return name.lower(), "\n".join(lines_out)


def build_products_page(cleaned_file_paths):
    """
    Scans every cleaned page for product-card paragraphs and consolidates
    them into one authoritative catalog file, deduplicated by product name.
    Gives 'what products do you sell' queries a single strong target
    instead of relying on scattered mentions to individually win ranking.
    """
    best_entries = {}  # name -> (score, entry_text)

    for file_path in cleaned_file_paths:
        if file_path.stem == "products":
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        _, body = read_body(text) if "Source URL:" in text else ("", text)
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]

        for p in paragraphs:
            result = extract_product_entry(p)
            if not result:
                continue
            key, entry = result
            score = entry.count("\n")  # more fields = richer entry
            if key not in best_entries or score > best_entries[key][0]:
                best_entries[key] = (score, entry)

    if not best_entries:
        print("No product-shaped entries found — skipping products.txt")
        return

    out_path = CLEANED_DIR / "products.txt"
    header = "Source URL: internal://product-catalog\n" + "=" * 50 + "\n\n"
    body = "\n\n".join(entry for _, entry in best_entries.values())

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + body)

    print(f"Built consolidated catalog -> '{out_path.relative_to(PROJECT_ROOT)}' ({len(best_entries)} unique product(s))")


def main():
    if not RAW_DIR.exists():
        print(f"Error: {RAW_DIR} does not exist.")
        return

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    raw_files = list(RAW_DIR.glob("*.txt"))
    print(f"Found {len(raw_files)} raw files to clean...\n")
    if not raw_files:
        return

    print("Scanning for repeated nav/footer boilerplate across pages...")
    boilerplate = build_boilerplate_index(raw_files)
    print(f"Identified {len(boilerplate)} site-wide boilerplate line(s).\n")

    cleaned_paths = []
    for file_path in raw_files:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        cleaned_text = clean_file_content(raw_text, boilerplate)
        out_path = CLEANED_DIR / file_path.name

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        cleaned_paths.append(out_path)
        content_chars = len(cleaned_text.split("=" * 50, 1)[-1].strip()) if "=" * 50 in cleaned_text else len(cleaned_text)
        print(f"Cleaned '{file_path.name}' -> '{out_path.relative_to(PROJECT_ROOT)}' ({content_chars} chars)")

    print()
    build_products_page(cleaned_paths)
    print("\nData cleaning complete.")


if __name__ == "__main__":
    main()