import logging
import re

from bs4 import BeautifulSoup
from retry import retry


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


@retry()
def parse_book(session, book_id):
    logging.basicConfig()
    response = session.get(f"https://www.goodreads.com/book/show/{book_id}")
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1", id="bookTitle").get_text().replace("\n", "").strip()
    edition = soup.find("span", attrs={"itemprop": "bookFormat"}).get_text().strip()
    try:
        language = soup.find("div", attrs={"itemprop": "inLanguage"}).get_text().strip()
    except AttributeError:
        language = None
    timeline_html = soup.find_all("div", class_="readingTimeline__text")

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

            book.append(event)
    print(f"Parsed '{title}' (id: {book_id})")
    return book
