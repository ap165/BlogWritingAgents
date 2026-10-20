import re
from urllib.parse import quote


def count_words(text: str) -> dict:
    """Count the words in a blog article or text."""
    words = re.findall(r"\b[\w'-]+\b", text)
    return {"word_count": len(words)}


def check_seo_lengths(
    title: str,
    meta_description: str,
    slug: str,
) -> dict:
    """Check title, meta description and slug lengths."""

    return {
        "title_length": len(title),
        "title_ok": 30 <= len(title) <= 60,
        "meta_description_length": len(meta_description),
        "meta_description_ok": 120 <= len(meta_description) <= 160,
        "slug_length": len(slug),
        "slug_ok": (
            len(slug) <= 75
            and bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug))
        ),
    }
