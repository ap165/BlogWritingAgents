from typing import Any, Dict, List, Union
from bs4 import BeautifulSoup
from requests import get

BASE_URL = "https://trends.google.com/trending/rss"

country_codes = ["US", "IN", "GB", "DE", "JP", "FR", "CA", "AU", "BR", "KR"]

TRENDING_CATEGORY_MAP = {
    0: "All Categories",
    1: "Autos and Vehicles",
    2: "Beauty and Fashion",
    3: "Business and Finance",
    4: "Entertainment",
    5: "Food and Drink",
    6: "Games",
    7: "Health",
    8: "Hobbies and Leisure",
    9: "Jobs and Education",
    10: "Law and Government",
    11: "Pets and Animals",
    12: "Politics",
    13: "Science",
    14: "Shopping",
    15: "Sports",
    16: "Technology",
    17: "Travel and Transportation",
    18: "Other",
    20: "Climate",
}

# Reverse map so the agent can pass either an integer ID (16) or a name ("Technology")
CATEGORY_NAME_TO_ID = {v.lower(): k for k, v in TRENDING_CATEGORY_MAP.items()}


def get_trends(
    country: str = "US", category: Union[int, str] = 0
) -> List[Dict[str, Any]]:
  """Fetches currently trending search queries from Google Trends RSS feed.

  Args:
      country: Two-letter ISO country code (e.g., 'US', 'IN', 'GB', 'DE', 'JP').
      category: Category ID (int) or Category Name (str) from
        TRENDING_CATEGORY_MAP. Defaults to 0 (All Categories).

  Returns:
      A list of dictionaries containing the trend title, approximate traffic,
      publication date, and related news articles.
  """
  country = country.upper().strip()
  if country not in country_codes:
    return [
        {
            "error": (
                f"Invalid country code '{country}'. Supported codes:"
                f" {country_codes}"
            )
        }
    ]

  # Resolve category if the agent passes a string name like "Technology" instead of 16
  cat_id = 0
  if isinstance(category, str):
    cat_id = CATEGORY_NAME_TO_ID.get(category.lower().strip(), 0)
  elif isinstance(category, int) and category in TRENDING_CATEGORY_MAP:
    cat_id = category

  params = {"geo": country}
  if cat_id != 0:
    params["category"] = cat_id

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }

  try:
    response = get(BASE_URL, params=params, headers=headers, timeout=10)
    response.raise_for_status()
  except Exception as e:
    return [{"error": f"Failed to fetch trends for {country}: {str(e)}"}]

  # Parse the RSS XML using BeautifulSoup
  soup = BeautifulSoup(response.content, "xml")
  items = soup.find_all("item")

  trends_list = []
  for item in items:
    title = item.find("title").text if item.find("title") else ""
    traffic = (
        item.find("ht:approx_traffic").text
        if item.find("ht:approx_traffic")
        else "N/A"
    )
    pub_date = item.find("pubDate").text if item.find("pubDate") else ""

    # Extract related news articles attached to the trend
    news_items = []
    for news in item.find_all("ht:news_item"):
      news_title = (
          news.find("ht:news_item_title").text
          if news.find("ht:news_item_title")
          else ""
      )
      news_url = (
          news.find("ht:news_item_url").text
          if news.find("ht:news_item_url")
          else ""
      )
      news_source = (
          news.find("ht:news_item_source").text
          if news.find("ht:news_item_source")
          else ""
      )
      if news_title:
        news_items.append(
            {"title": news_title, "url": news_url, "source": news_source}
        )

    trends_list.append({
        "query": title,
        "approx_traffic": traffic,
        "pub_date": pub_date,
        "country": country,
        "category": TRENDING_CATEGORY_MAP.get(cat_id, "All Categories"),
        "related_news": news_items,
    })

  return trends_list