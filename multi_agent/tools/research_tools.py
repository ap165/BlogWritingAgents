import requests
from bs4 import BeautifulSoup

def load_web_page(url: str) -> dict:
    """Fetch a public web page and return its readable text."""

    if not url.startswith(("https://", "http://")):
        return {"error": "Only HTTP and HTTPS URLs are allowed."}

    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "BlogResearchBot/1.0"},
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for element in soup(
            ["script", "style", "nav", "footer", "header"]
        ):
            element.decompose()

        return {
            "url": response.url,
            "title": soup.title.get_text(" ", strip=True)
            if soup.title else "",
            "text": soup.get_text(" ", strip=True)[:15000],
        }

    except requests.RequestException as exc:
        return {"error": f"Could not load page: {exc}"}
