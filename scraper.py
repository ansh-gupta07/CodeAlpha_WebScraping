"""
CodeAlpha Data Analytics Internship - Task 1: Web Scraping
Scrapes book data from https://books.toscrape.com (a site built for scraping practice).

Collects: title, price, star rating, availability, product URL, and (optionally,
from each book's detail page) category, UPC and description.

Usage:
    python scraper.py                  # all 50 listing pages, basic fields
    python scraper.py --details        # also visit each book page (slower, ~1000 requests)
    python scraper.py --pages 3        # quick test run
"""
import argparse
import csv
import logging
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/catalogue/"
PAGE_URL = BASE_URL + "page-{}.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (CodeAlpha internship learning project)"}
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_soup(session, url, retries=3, delay=1.0):
    """Fetch a URL and return BeautifulSoup, retrying on failure. Returns None if all fail."""
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            resp.encoding = "utf-8"  # avoids garbled '£' symbols
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as exc:
            log.warning("Attempt %d/%d failed for %s: %s", attempt, retries, url, exc)
            time.sleep(delay * attempt)
    return None


def parse_listing(soup):
    """Extract one record per book from a listing page."""
    records = []
    for card in soup.select("article.product_pod"):
        link = card.h3.a
        rating_word = card.select_one("p.star-rating")["class"][1]
        price_text = card.select_one("p.price_color").get_text(strip=True)
        records.append({
            "title": link["title"],
            "price_gbp": float(price_text.replace("£", "")),
            "rating": RATING_MAP.get(rating_word),
            "in_stock": "In stock" in card.select_one("p.availability").get_text(),
            "url": urljoin(BASE_URL, link["href"]),
        })
    return records


def parse_detail(soup):
    """Extract extra fields from a single book's page."""
    crumbs = soup.select("ul.breadcrumb li a")
    category = crumbs[-1].get_text(strip=True) if crumbs else None
    table = {r.th.get_text(strip=True): r.td.get_text(strip=True)
             for r in soup.select("table.table-striped tr")}
    desc_tag = soup.select_one("#product_description ~ p")
    return {
        "category": category,
        "upc": table.get("UPC"),
        "num_reviews": int(table.get("Number of reviews", 0)),
        "description": desc_tag.get_text(strip=True) if desc_tag else None,
    }


def scrape(max_pages, details, delay):
    session = requests.Session()
    books = []
    for page in range(1, max_pages + 1):
        soup = get_soup(session, PAGE_URL.format(page))
        if soup is None:
            log.info("No page %d - stopping.", page)
            break
        page_books = parse_listing(soup)
        log.info("Page %d: %d books", page, len(page_books))
        books.extend(page_books)
        time.sleep(delay)  # be polite to the server

    if details:
        for i, book in enumerate(books, 1):
            soup = get_soup(session, book["url"])
            if soup:
                book.update(parse_detail(soup))
            if i % 50 == 0:
                log.info("Detail pages done: %d/%d", i, len(books))
            time.sleep(delay)
    return books


def clean(books):
    """Remove duplicate books (by URL) and report missing values."""
    seen, unique = set(), []
    for b in books:
        if b["url"] not in seen:
            seen.add(b["url"])
            unique.append(b)
    log.info("Removed %d duplicate rows", len(books) - len(unique))
    for col in unique[0]:
        missing = sum(1 for b in unique if b.get(col) in (None, ""))
        log.info("Missing in %-12s: %d", col, missing)
    return unique


def save_csv(books, path):
    fields = list(books[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(books)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=50, help="listing pages to scrape (max 50)")
    parser.add_argument("--details", action="store_true", help="also scrape each book's detail page")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    parser.add_argument("--out", default="books_dataset.csv")
    args = parser.parse_args()

    books = scrape(args.pages, args.details, args.delay)
    if not books:
        log.error("Nothing scraped. Check your internet connection.")
        return
    books = clean(books)
    save_csv(books, args.out)
    log.info("Saved %d books to %s", len(books), args.out)

    n = len(books)
    print("\nSummary")
    print("-------")
    print(f"Books scraped : {n}")
    print(f"Average price : GBP {sum(b['price_gbp'] for b in books) / n:.2f}")
    print(f"Average rating: {sum(b['rating'] for b in books) / n:.2f} / 5")
    print(f"In stock      : {sum(b['in_stock'] for b in books) / n:.0%}")


if __name__ == "__main__":
    main()
