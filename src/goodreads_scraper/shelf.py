import math
import re
import time

from bs4 import BeautifulSoup
import requests

from .utils import progress


def get_number_books(soup):
    return int(
        re.search(
            r"\(([0-9]*)\)", soup.find("a", class_="selectedShelf").get_text()
        ).group(1)
    )


def get_number_pages(num_books, limit):
    if limit == 0 or limit >= num_books:
        return math.ceil(num_books / 30)
    else:
        return math.ceil(limit / 30)


def extract_fields(row, iteration):
    book = {}
    # Title
    book["title"] = row.select("td.field.title")[0].div.a["title"]

    # Author
    book["author"] = (
        row.select("td.field.author")[0].div.get_text(strip=True).replace("*", "")
    )

    # Pages
    num_pages_text = row.select("td.field.num_pages")[0].get_text(strip=True)
    book["num_pages"] = re.search(r"([0-9]+)", num_pages_text).group(0)

    # Avg. Rating
    book["avg_rating"] = row.select("td.field.avg_rating")[0].div.get_text(strip=True)

    # Number Ratings
    book["num_ratings"] = (
        row.select("td.field.num_ratings")[0].div.get_text(strip=True).replace(",", "")
    )

    # My Rating
    book["rating"] = int(row.select("td.field.rating")[0].div.div["data-rating"])

    # Read Count
    book["read_count"] = int(
        row.select("td.field.read_count")[0].div.get_text(strip=True)
    )

    # Started Date
    start_date = (
        row.select("td.field.date_started")[0]
        .div.get_text(strip=True)
        .split("[edit]")[iteration]
    )
    book["event_start_date"] = None if start_date == "not set" else start_date

    # Finished Date
    finish_date = (
        row.select("td.field.date_read")[0]
        .div.get_text(strip=True)
        .split("[edit]")[iteration]
    )
    book["event_finish_date"] = None if finish_date == "not set" else finish_date

    # Date Added
    book["date_added"] = row.select("td.field.date_added")[0].div.get_text(strip=True)

    # Edition
    book["edition"] = (
        row.select("td.field.format")[0].div.get_text(strip=True).replace("[edit]", "")
    )

    # Date Publication Edition
    book["date_pub_edition"] = row.select("td.field.date_pub_edition")[0].div.get_text(
        strip=True
    )

    # Book ID
    book["id"] = row.select("td.field.rating")[0].div.div["data-resource-id"]

    # Date Publication Work
    book["date_pub"] = row.select("td.field.date_pub")[0].div.get_text(strip=True)

    # Work ID
    work_id_link = row.select("td.field.format")[0].a["href"]
    book["work_id"] = (
        re.search(r"([0-9]+)", work_id_link).group(0) if work_id_link else None
    )
    return book


def parse_book_row(row):
    row_books = []
    read_count = int(row.select("td.field.read_count")[0].div.get_text(strip=True))

    for iteration in range(0, read_count):
        row_books.append(extract_fields(row, iteration))
    return row_books


def parse_shelf_page(page_soup):
    shelf_books = []

    book_rows = page_soup.find_all("tr", id=re.compile("^review_"))
    for book_row in book_rows:
        shelf_books += parse_book_row(book_row)

    return shelf_books


def scrape_shelf(session, shelf_url, limit=0):
    response = session.get(shelf_url)
    first_page_soup = BeautifulSoup(response.text, "html.parser")

    num_books = get_number_books(first_page_soup)
    num_pages = get_number_pages(num_books, limit)

    msg = "Scraping pages in shelf: "
    progress(0, num_pages, msg)

    books = parse_shelf_page(first_page_soup)
    progress(1, num_pages, msg)

    for page_num in range(2, num_pages + 1):
        response = session.get(f"{shelf_url}&page={page_num}")
        page_soup = BeautifulSoup(response.text, "html.parser")

        books += parse_shelf_page(page_soup)
        progress(page_num, num_pages, msg)

    scraped_ids = books[0:limit] if limit else books

    print(
        f"Shelf scraped: {len(scraped_ids)} books retrieved.",
    )
    return scraped_ids
