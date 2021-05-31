import math
import re

from bs4 import BeautifulSoup


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


def parse_shelf_page(page_soup):
    page_book_ids = []

    book_rows = page_soup.find_all("td", class_="field cover")

    for book_row in book_rows:
        book_div = book_row.div.div

        if book_div["data-resource-type"] == "Book":
            page_book_ids.append(int(book_div["data-resource-id"]))

    return page_book_ids


def scrape_shelf(session, shelf_url, limit=0):
    print(f"Scraping {shelf_url}")
    response = session.get(shelf_url)
    first_page_soup = BeautifulSoup(response.text, "html.parser")

    num_books = get_number_books(first_page_soup)
    num_pages = get_number_pages(num_books, limit)

    shelf_book_ids = parse_shelf_page(first_page_soup)

    for page_num in range(2, num_pages + 1):
        response = session.get(f"{shelf_url}?page={page_num}")
        page_soup = BeautifulSoup(response.text, "html.parser")

        shelf_book_ids += parse_shelf_page(page_soup)

    scraped_ids = shelf_book_ids[0:limit] if limit else shelf_book_ids

    print(
        f"\nShelf scraped: {len(scraped_ids)}/{num_books} book ids retrieved.",
    )
    return scraped_ids
