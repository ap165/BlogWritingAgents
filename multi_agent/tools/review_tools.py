import re
from difflib import SequenceMatcher
from urllib.parse import urlparse
import requests


def readability_score(text: str) -> dict:
    """Estimate readability using average sentence and word lengths."""

    words = re.findall(r"\b[\w'-]+\b", text)
    sentences = [
        s for s in re.split(r"[.!?]+", text) if s.strip()
    ]

    if not words or not sentences:
        return {"error": "Not enough text to score."}

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "average_words_per_sentence": round(
            len(words) / len(sentences), 2
        ),
        "average_characters_per_word": round(
            sum(map(len, words)) / len(words), 2
        ),
    }


def similarity_check(text: str, published_text: str) -> dict:
    """Compare a draft against one supplied published article."""

    similarity = SequenceMatcher(
        None, text.casefold(), published_text.casefold()
    ).ratio()

    return {
        "similarity_percent": round(similarity * 100, 2),
        "warning": similarity >= 0.80,
    }


def check_links(url: str) -> dict:
    """Check whether a public HTTP or HTTPS URL responds."""

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return {"url": url, "error": "Invalid URL."}

    try:
        response = requests.get(
            url,
            timeout=8,
            stream=True,
            allow_redirects=False,
        )
        result = {
            "url": url,
            "status_code": response.status_code,
            "reachable": 200 <= response.status_code < 400,
        }
        response.close()
        return result
    except requests.RequestException as exc:
        return {"url": url, "error": str(exc)}
