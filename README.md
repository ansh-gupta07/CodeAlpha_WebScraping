# CodeAlpha_WebScraping

**CodeAlpha Data Analytics Internship, Task 1: Web Scraping**

Scrapes the book catalogue at [books.toscrape.com](https://books.toscrape.com) (a legal practice site)
using `requests` and `BeautifulSoup`, and builds a clean CSV dataset ready for analysis.

## Dataset fields
| Field | Description |
|---|---|
| title | Book title |
| price_gbp | Price in British pounds |
| rating | Star rating (1-5) |
| in_stock | True/False |
| url | Book page link |
| category, upc, num_reviews, description | Only with `--details` |

## How it works
1. Loops through the paginated listing (`page-1.html` ... `page-50.html`).
2. Parses each `article.product_pod` for title, price, rating and stock.
3. Optionally visits each book's page for category, UPC and description.
4. Retries failed requests, waits between requests, removes duplicates and reports missing values.
5. Saves to `books_dataset.csv`.

## Run it
```bash
pip install -r requirements.txt
python scraper.py --pages 3        # quick test
python scraper.py                  # 1,000 books, basic fields
python scraper.py --details        # 1,000 books with category/description (about 10 min)
```

## Ideas for next tasks
The CSV works for Task 2 (EDA: price vs rating, category distribution) and Task 3 (visualization).
