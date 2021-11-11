import re
import sys

from bs4 import BeautifulSoup
from retry import retry

from .utils import progress


GR_BASE_BOOK_URL = "https://www.goodreads.com/book/show/"


def parse_timeline_event(event_raw):
    event_string = re.sub(r"[\r\n]+", "|", event_raw)
    event_string = re.sub(r"[|–|]+", "|", event_string)
    event_string = re.sub(r"[():]", "", event_string)

    date, status, _ = (
        event_string.split("|")[0].strip(),
        event_string.split("|")[1].strip(),
        event_string.split("|")[2:],
    )

    if status == "Add a date":
        status = date
        date = None
        shelf = None
        try:
            edition = _[0]
        except IndexError:
            edition = None
    elif status == "Shelved as":
        shelf = _[0]
        try:
            edition = _[1]
        except IndexError:
            edition = None
    else:
        shelf = None
        try:
            edition = _[0]
        except IndexError:
            edition = None

    return {
        "event_date": date,
        "event_status": status,
        "event_edition": edition,
        "event_shelf": shelf,
    }


@retry(tries=10, delay=2)
def scrape_book(session, book_id):
    response = session.get(f"{GR_BASE_BOOK_URL}{book_id}")

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("h1", id="bookTitle").get_text().replace("\n", "").strip()
    edition = soup.find("span", attrs={"itemprop": "bookFormat"}).get_text().strip()
    try:
        language = soup.find("div", attrs={"itemprop": "inLanguage"}).get_text().strip()
    except AttributeError:
        language = None
    timeline_html = soup.find_all("div", class_="readingTimeline__text")
    work_id_link = soup.find(class_="otherEditionsActions").a["href"]
    work_id = re.search(r"([0-9]+)", work_id_link).group(0) if work_id_link else None

    book = []
    for div in timeline_html[::-1]:
        if div.get_text():
            event = parse_timeline_event(div.get_text().strip())

            a_tag = div.find(href=re.compile("/book/show/.*"))
            event["event_id"] = (
                re.search(r"([0-9]+)", a_tag["href"]).group(1) if a_tag else None
            )

            event["title"] = title
            event["book_id"] = book_id
            event["edition"] = edition
            event["language"] = language
            event["work_id"] = work_id

            book.append(event)
    return book


def scrape_books(session, book_ids):
    books = []
    failed_ids = []

    msg = "Scraping books: "
    i = 0
    num_books = len(book_ids)
    progress(i, num_books, msg)

    for id in book_ids:
        try:
            books += scrape_book(session, id)
        except:
            failed_ids.append(id)

        i += 1
        progress(i, num_books, msg)

    if len(failed_ids) != 0:
        print(
            f"Completed with errors: scraped {num_books - len(failed_ids)}, failed {len(failed_ids)} book(s)"
        )
        print(f"ID(s) of failed book(s): {failed_ids}")
    else:
        print(f"Completed: scraped {num_books - len(failed_ids)} book(s)")
    return books
