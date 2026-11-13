import os
import re
import threading
import time
from typing import Any, Dict, List
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

# Load from your .env file (or paste directly for local testing)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    "windows:multi_agent_trend_analyzer:v1.0.0 (by /u/_ap165)",
)

_token_lock = threading.Lock()
_cached_token: str = ""
_token_expiry: float = 0.0


def _get_oauth_token() -> str:
  """Fetches and caches a Reddit OAuth2 token in a thread-safe way."""
  global _cached_token, _token_expiry
  with _token_lock:
    if _cached_token and time.time() < _token_expiry:
      return _cached_token

    auth = HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {"grant_type": "client_credentials"}
    headers = {"User-Agent": REDDIT_USER_AGENT}

    resp = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=auth,
        data=data,
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    token_data = resp.json()

    _cached_token = token_data["access_token"]
    # Refresh 60 seconds before actual expiration (usually 3600s)
    _token_expiry = time.time() + int(token_data.get("expires_in", 3600)) - 60
    return _cached_token


def search_reddit(
    query: str,
    subreddit: str = "all",
    sort: str = "relevance",
    time_filter: str = "week",
    limit: int = 10,
) -> List[Dict[str, Any]]:
  """Searches Reddit via Official OAuth API and returns clean results for an AI agent.

  Args:
      query: The search keywords or topic (e.g., 'FastAPI performance', 'AI
        agents').
      subreddit: Specific subreddit name without 'r/' (e.g., 'python',
        'technology'). Defaults to 'all' for a site-wide search.
      sort: Sorting method - 'relevance', 'hot', 'top', 'new', or 'comments'.
        Defaults to 'relevance'.
      time_filter: Time range - 'hour', 'day', 'week', 'month', 'year', or
        'all'. Defaults to 'week'.
      limit: Maximum number of posts to return (1 to 25). Defaults to 10.

  Returns:
      A list of dictionaries containing post title, subreddit, author, score,
      comment count, URL, and a clean text snippet.
  """
  subreddit = re.sub(
      r"^/?r/", "", subreddit.strip(), flags=re.IGNORECASE
  ).strip("/")
  if not subreddit:
    subreddit = "all"
  limit = max(1, min(limit, 25))

  try:
    token = _get_oauth_token()
  except Exception as e:
    return [{"error": f"Reddit OAuth authentication failed: {str(e)}"}]

  url = f"https://oauth.reddit.com/r/{subreddit}/search"
  headers = {
      "Authorization": f"bearer {token}",
      "User-Agent": REDDIT_USER_AGENT,
  }
  params = {
      "q": query,
      "restrict_sr": "0" if subreddit.lower() == "all" else "1",
      "sort": sort,
      "t": time_filter,
      "limit": limit,
      "raw_json": "1",  # Tells Reddit not to HTML-escape characters like & or <
  }

  try:
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    children = resp.json().get("data", {}).get("children", [])
  except Exception as e:
    return [{"error": f"Failed to search Reddit for '{query}': {str(e)}"}]

  results = []
  for child in children:
    post = child.get("data", {})
    selftext = post.get("selftext", "").strip()
    # If it's a link post with no body text, include the external link target
    if not selftext and post.get("url"):
      selftext = f"[External Link: {post.get('url')}]"

    results.append({
        "title": post.get("title", "No Title"),
        "subreddit": post.get("subreddit_name_prefixed", f"r/{subreddit}"),
        "author": post.get("author", "unknown"),
        "score": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "url": f"https://www.reddit.com{post.get('permalink', '')}",
        "published": time.strftime(
            "%Y-%m-%d %H:%M:%S UTC",
            time.gmtime(post.get("created_utc", 0)),
        ),
        "snippet": selftext[:500] + "..." if len(selftext) > 500 else selftext,
    })

  return results