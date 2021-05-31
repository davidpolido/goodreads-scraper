from bs4 import BeautifulSoup
import requests

LOGIN_URL = "https://www.goodreads.com/user/sign_in"


def get_authenticity_token(html):
    soup = BeautifulSoup(html, "html.parser")
    token = soup.find("input", attrs={"name": "authenticity_token"})
    if not token:
        print("could not find `authenticity_token` on login form")
    return token.get("value").strip()


def get_login_n(html):
    # there is a hidden input named `n` that also needs to be passed
    soup = BeautifulSoup(html, "html.parser")
    n = soup.find("input", attrs={"name": "n"})
    if not n:
        print("could not find `n` on login form")
    return n.get("value").strip()


def login(user_email, user_password, login_url=LOGIN_URL):
    payload = {
        "user[email]": user_email,
        "user[password]": user_password,
        "utf8": "&#x2713;",
    }

    session = requests.Session()
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    response = session.get(login_url)

    token = get_authenticity_token(response.text)
    n = get_login_n(response.text)
    payload.update({"authenticity_token": token, "n": n})

    print(f"Attempting to log in as {user_email}...", end="")
    p = session.post(login_url, data=payload)
    if p.ok:
        print(f"\rAttempting to log in as {user_email} - Done!", end="")
        return session
    else:
        print("\nProblem logging in. Please try again.")
        return None
