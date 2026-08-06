import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# 1. Configurable Target Domain (Works for any website)
BASE_URL = "https://lumeluxe.pk"

# Global exclusion rules for non-knowledge paths
EXCLUDE_PATTERNS = [
    r"/cart",
    r"/account",
    r"/checkout",
    r"/search",
    r"/collections/all\?",
    r"/login",
    r"/register",
    r"/forget-?password",
    r"/reset",
    r"/dashboard",
    r"/orders",
    r"\.json$",
    r"\.js$",
    r"\.css$",
    r"\.png$",
    r"\.jpg$",
    r"\.jpeg$",
    r"\.svg$"
]

RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_domain(url: str) -> str:
    """Extract base network location."""
    return urlparse(url).netloc


def is_valid_internal_url(target_url: str, base_domain: str) -> bool:
    """Ensures link stays within target domain and avoids utility endpoints."""
    parsed = urlparse(target_url)
    if parsed.netloc and parsed.netloc != base_domain:
        return False

    path = parsed.path
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return False
    return True


def clean_html(soup: BeautifulSoup) -> str:
    """Strips script/style elements and extracts readable text."""
    for element in soup(["script", "style", "noscript", "svg", "iframe"]):
        element.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    clean_lines = [line for line in lines if line]
    return "\n".join(clean_lines)


def crawl_website(start_url: str, max_pages: int = 15):
    """Generic crawler that starts strictly from the homepage URL."""
    base_domain = get_domain(start_url)
    visited = set()
    to_visit = {start_url}
    scraped_count = 0

    print(f" Starting dynamic crawl on target domain: {base_domain}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        while to_visit and scraped_count < max_pages:
            current_url = to_visit.pop()

            # Clean query strings/hash fragments for strict deduplication
            clean_current_url = current_url.split("?")[0].split("#")[0]
            if clean_current_url in visited:
                continue

            visited.add(clean_current_url)
            print(f"\n Fetching [{scraped_count + 1}/{max_pages}]: {current_url}")

            try:
                response = page.goto(
                    current_url, wait_until="domcontentloaded", timeout=30000
                )
                status = response.status if response else "Unknown"
                print(f"   ↳ Status Code: {status}")

                # Allow full client-side rendering / Shopify policy JS loads
                time.sleep(2)

                content = page.content()
                soup = BeautifulSoup(content, "html.parser")

                # Parse and discover new internal links from the rendered DOM
                for anchor in soup.find_all("a", href=True):
                    full_link = urljoin(start_url, anchor["href"])
                    clean_link = full_link.split("?")[0].split("#")[0]
                    if clean_link not in visited and is_valid_internal_url(
                        clean_link, base_domain
                    ):
                        to_visit.add(clean_link)

                # Extract cleaned plain text
                text_content = clean_html(soup)
                print(f"   ↳ Cleaned Text Length: {len(text_content)} characters")

                if len(text_content) < 50:
                    print("    Skipped (Content too short)")
                    continue

                # Generate clean filenames based on URL path
                url_path = urlparse(current_url).path.strip("/")
                if not url_path:
                    filename = "homepage"
                else:
                    filename = url_path.replace("/", "_")

                file_path = RAW_DATA_DIR / f"{filename}.txt"

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"Source URL: {current_url}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(text_content)

                print(f"    Saved -> {file_path}")
                scraped_count += 1

            except Exception as e:
                print(f"    Error fetching {current_url}: {e}")

        browser.close()

    print(f"\n Crawling finished! Saved {scraped_count} documents in '{RAW_DATA_DIR}'.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    crawl_website(target, max_pages=15)