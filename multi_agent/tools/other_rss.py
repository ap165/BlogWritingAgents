from typing import Any, Dict, List, Union
from bs4 import BeautifulSoup
from requests import get

POPULAR_FEEDS = {
    "hacker_news": "https://hnrss.org/frontpage",
    "techcrunch": "https://techcrunch.com/feed/",
    "the_verge": "https://www.theverge.com/rss/index.xml",
    "ars_technica": "https://feeds.arstechnica.com/arstechnica/index",
    "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "arxiv_cs_ai": "https://rss.arxiv.org/rss/cs.AI",
    "github_blog": "https://github.blog/feed/",
    "lobsters": "https://lobste.rs/rss",
}


def _fetch_single_feed(
    source_name: str,
    feed_url: str,
    limit: int = 10,
    max_summary_length: int = 400,
) -> Dict[str, Any]:
  """Internal helper to fetch and normalize a single RSS or Atom XML feed."""
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
      ),
      "Accept": (
          "application/rss+xml, application/atom+xml, application/xml,"
          " text/xml, */*"
      ),
  }

  try:
    response = get(feed_url, headers=headers, timeout=12)
    response.raise_for_status()
  except Exception as e:
    return {
        "source": source_name,
        "feed_url": feed_url,
        "error": f"Failed to fetch feed: {str(e)}",
    }

  soup = BeautifulSoup(response.content, "xml")

  feed_title_tag = soup.find("title")
  feed_title = (
      feed_title_tag.text.strip() if feed_title_tag else source_name
  )

  # Support both RSS (<item>) and Atom (<entry>, used by The Verge)
  raw_entries = soup.find_all("item")
  if not raw_entries:
    raw_entries = soup.find_all("entry")

  if not raw_entries:
    return {
        "source": source_name,
        "feed_url": feed_url,
        "error": "No valid RSS <item> or Atom <entry> tags found.",
    }

  items: List[Dict[str, Any]] = []
  for entry in raw_entries[: max(1, min(limit, 50))]:
    # 1. Title
    title_tag = entry.find("title")
    title = title_tag.text.strip() if title_tag else "Untitled"

    # 2. Link (Handles both RSS <link>text</link> and Atom <link href="..."/>)
    link = ""
    for l_tag in entry.find_all("link"):
      if l_tag.get("href"):
        if l_tag.get("rel") in [None, "alternate"]:
          link = l_tag.get("href").strip()
          break
      elif l_tag.text:
        link = l_tag.text.strip()
        break

    if not link:
      guid_tag = entry.find("guid")
      if guid_tag and guid_tag.text.strip().startswith("http"):
        link = guid_tag.text.strip()

    # 3. Publication Date
    pub_date = ""
    for date_tag in ["pubDate", "published", "updated", "dc:date", "date"]:
      d_tag = entry.find(date_tag)
      if d_tag and d_tag.text:
        pub_date = d_tag.text.strip()
        break

    # 4. Author / Creator (Handles <dc:creator>, <author><name>, and <author>)
    author = ""
    author_tag = (
        entry.find("dc:creator")
        or entry.find("creator")
        or entry.find("author")
    )
    if author_tag:
      name_sub = author_tag.find("name")
      author = (
          name_sub.text.strip() if name_sub else author_tag.text.strip()
      )

    # 5. Summary / Description (Strips HTML & CDATA from TechCrunch, GitHub, ArXiv, etc.)
    raw_html = ""
    for content_tag in [
        "description",
        "summary",
        "content",
        "content:encoded",
    ]:
      c_tag = entry.find(content_tag)
      if c_tag and c_tag.text:
        raw_html = c_tag.text
        break

    clean_summary = ""
    if raw_html:
      html_soup = BeautifulSoup(raw_html, "html.parser")
      clean_summary = html_soup.get_text(separator=" ", strip=True)
      if len(clean_summary) > max_summary_length:
        clean_summary = clean_summary[:max_summary_length].rstrip() + "..."

    # 6. Categories / Tags
    categories = []
    for cat in entry.find_all("category"):
      cat_val = cat.get("term") or cat.get("label") or cat.text
      if cat_val and cat_val.strip():
        categories.append(cat_val.strip())

    # 7. Hacker News / Lobsters Comments URL (if present)
    comments_tag = entry.find("comments")
    comments_url = comments_tag.text.strip() if comments_tag else ""

    item_data = {
        "title": title,
        "url": link,
        "published": pub_date,
        "author": author or "Unknown",
        "summary": clean_summary,
    }
    if categories:
      item_data["categories"] = categories[:5]
    if comments_url:
      item_data["comments_url"] = comments_url

    items.append(item_data)

  return {
      "source": source_name,
      "feed_title": feed_title,
      "feed_url": feed_url,
      "item_count": len(items),
      "items": items,
  }


def get_rss_feed(
    source: str = "hacker_news",
    limit: int = 10,
    max_summary_length: int = 400,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
  """Fetches articles from popular tech/news RSS presets or any custom RSS/Atom URL.

  Args:
      source: One of the preset keys ('hacker_news', 'techcrunch', 'the_verge',
        'ars_technica', 'bbc_world', 'arxiv_cs_ai', 'github_blog', 'lobsters'),
        'all' to fetch top items from every preset feed, or any direct
        'http://' / 'https://' RSS feed URL. Defaults to 'hacker_news'.
      limit: Maximum number of items to return per feed (1 to 50). Defaults to
        10.
      max_summary_length: Maximum character length of each article's summary
        snippet. Defaults to 400.

  Returns:
      A dictionary with feed metadata and items (or a list of dictionaries if
      source='all').
  """
  clean_source = source.strip()
  lower_source = clean_source.lower().replace(" ", "_").replace("-", "_")

  # Case 1: Fetch from ALL preset feeds at once
  if lower_source == "all":
    all_results = []
    # Cap per-feed limit when pulling all 8 feeds so agent context doesn't overflow
    per_feed_limit = min(limit, 5)
    for key, url in POPULAR_FEEDS.items():
      all_results.append(
          _fetch_single_feed(key, url, per_feed_limit, max_summary_length)
      )
    return all_results

  # Case 2: Fetch from a named preset in POPULAR_FEEDS
  if lower_source in POPULAR_FEEDS:
    target_url = POPULAR_FEEDS[lower_source]
    return _fetch_single_feed(
        lower_source, target_url, limit, max_summary_length
    )

  # Case 3: Fetch from a custom external URL passed by the agent
  if clean_source.startswith(("http://", "https://")):
    return _fetch_single_feed(
        "custom_url", clean_source, limit, max_summary_length
    )

  # Case 4: Invalid preset name
  return {
      "error": (
          f"Unknown feed source '{source}'. Choose from"
          f" {list(POPULAR_FEEDS.keys())}, 'all', or provide a full http/https"
          " RSS URL."
      )
  }