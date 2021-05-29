import re

from bs4 import BeautifulSoup


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

    return {"date": date, "status": status, "edition": edition, "shelf": shelf}


def parse_book(session, book_id):
    response = session.get(f"https://www.goodreads.com/book/show/{book_id}")
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1", id="bookTitle").get_text().replace("\n", "").strip()
    edition = soup.find("span", attrs={"itemprop": "bookFormat"}).get_text().strip()
    timeline_html = soup.find_all("div", class_="readingTimeline__text")

    book = []
    for div in timeline_html[::-1]:
        if div.get_text():
            event = parse_timeline_event(div.get_text().strip())
            event["title"] = title

            event["book_id"] = book_id
            if not event["edition"]:
                event["edition"] = edition

            book.append(event)
    print(f"Parsed '{title}' (id: {book_id})")
    return book
