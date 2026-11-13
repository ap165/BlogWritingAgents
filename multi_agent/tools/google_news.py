from typing import Any, Dict, List
from bs4 import BeautifulSoup
from requests import get

NEWS_BASE_URL = "https://news.google.com/rss"

country_codes = ["US", "IN", "GB", "DE", "JP", "FR", "CA", "AU", "BR", "KR"]

VALID_NEWS_TOPICS = [
    "WORLD",
    "NATION",
    "BUSINESS",
    "TECHNOLOGY",
    "ENTERTAINMENT",
    "SPORTS",
    "SCIENCE",
    "HEALTH",
]


def search_news(
    query: str = "",
    topic: str = "",
    location: str = "",
    country: str = "IN",
    time_range: str = "24h",
    limit: int = 10,
) -> List[Dict[str, Any]]:
  """Searches Google News RSS feeds by keyword query, topic category, or geographic location.

  Args:
      query: Search keywords (e.g., 'AI agents', 'stock market'). Supports
        operators like 'OR', 'site:reuters.com', or 'intitle:OpenAI'. Leave
        empty if browsing by topic or location.
      topic: Major news category. Must be one of: 'WORLD', 'NATION', 'BUSINESS',
        'TECHNOLOGY', 'ENTERTAINMENT', 'SPORTS', 'SCIENCE', 'HEALTH'. Ignored if
        `query` is provided.
      location: Specific city or state name (e.g., 'Kolkata', 'New York') for
        local news. Ignored if `query` or `topic` is provided.
      country: Two-letter ISO country code for the news edition ('US', 'IN',
        'GB', 'DE', 'JP', 'FR', 'CA', 'AU', 'BR', 'KR'). Defaults to 'IN'.
      time_range: Recency filter applied to keyword queries (e.g., '1h', '12h',
        '24h', '7d', '30d'). Set to '' for all time. Defaults to '24h'.
      limit: Maximum number of news articles to return (1 to 100). Defaults to
        10.

  Returns:
      A list of dictionaries containing the clean headline, publisher name,
      publisher domain, publication timestamp, link, and related sub-articles.
  """
  country = country.upper().strip()
  if country not in country_codes:
    return [
        {
            "error": (
                f"Invalid country code '{country}'. Supported: {country_codes}"
            )
        }
    ]

  # Set Google News edition locale parameters
  params = {
      "hl": f"en-{country}",
      "gl": country,
      "ceid": f"{country}:en",
  }

  # Route to the right RSS endpoint based on agent input priority:
  # 1. Keyword Search -> 2. Topic Category -> 3. Geo Location -> 4. Top Headlines
  if query.strip():
    url = f"{NEWS_BASE_URL}/search"
    search_q = query.strip()
    if time_range.strip() and "when:" not in search_q:
      search_q += f" when:{time_range.strip()}"
    params["q"] = search_q

  elif topic.strip():
    clean_topic = topic.strip().upper()
    if clean_topic not in VALID_NEWS_TOPICS:
      return [
          {
              "error": (
                  f"Invalid topic '{topic}'. Must be one of:"
                  f" {VALID_NEWS_TOPICS}"
              )
          }
      ]
    url = f"{NEWS_BASE_URL}/headlines/section/topic/{clean_topic}"

  elif location.strip():
    clean_loc = location.strip().replace(" ", "%20")
    url = f"{NEWS_BASE_URL}/headlines/section/geo/{clean_loc}"

  else:
    url = NEWS_BASE_URL

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
      )
  }

  try:
    response = get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
  except Exception as e:
    return [{"error": f"Failed to fetch Google News: {str(e)}"}]

  soup = BeautifulSoup(response.content, "xml")
  items = soup.find_all("item")

  results = []
  for item in items[: min(limit, 100)]:
    raw_title = item.find("title").text if item.find("title") else ""
    link = item.find("link").text if item.find("link") else ""
    pub_date = item.find("pubDate").text if item.find("pubDate") else ""

    source_tag = item.find("source")
    source_name = source_tag.text.strip() if source_tag else "Unknown"
    source_url = source_tag.get("url", "") if source_tag else ""

    # Strip trailing " - Source Name" from the headline
    clean_title = raw_title
    suffix = f" - {source_name}"
    if source_name and raw_title.endswith(suffix):
      clean_title = raw_title[: -len(suffix)].strip()

    # Extract clustered sub-articles inside the HTML <description> tag
    related_coverage = []
    description_html = (
        item.find("description").text if item.find("description") else ""
    )
    if description_html:
      desc_soup = BeautifulSoup(description_html, "html.parser")
      for li in desc_soup.find_all("li"):
        a_tag = li.find("a")
        font_tag = li.find("font")
        if a_tag:
          sub_title = a_tag.get_text(strip=True)
          sub_source = font_tag.get_text(strip=True) if font_tag else ""
          if sub_title and sub_title != clean_title:
            related_coverage.append(
                {"headline": sub_title, "source": sub_source}
            )

    results.append({
        "headline": clean_title,
        "source": source_name,
        "publisher_domain": source_url,
        "published": pub_date,
        "url": link,
        "related_coverage": related_coverage[:3],  # Keep token footprint small
    })

  return results