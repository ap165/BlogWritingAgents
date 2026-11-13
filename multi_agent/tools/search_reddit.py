import os
import re
import threading
import time
from typing import Any, Dict, List

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()


# Reddit API configuration
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "").strip()
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "").strip()

REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    "windows:multi_agent_trend_analyzer:v1.0.0 (by /u/_ap165)",
)

REDDIT_OAUTH_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_BASE = "https://oauth.reddit.com"


# OAuth token cache
_token_lock = threading.Lock()
_cached_token: str = ""
_token_expiry: float = 0.0


def _get_oauth_token() -> str:
    """Fetch and cache a Reddit OAuth2 token safely."""

    global _cached_token, _token_expiry

    with _token_lock:
        if _cached_token and time.time() < _token_expiry:
            return _cached_token

        if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
            raise ValueError(
                "Reddit API credentials are missing. "
                "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET."
            )

        auth = HTTPBasicAuth(
            REDDIT_CLIENT_ID,
            REDDIT_CLIENT_SECRET,
        )

        data = {
            "grant_type": "client_credentials"
        }

        headers = {
            "User-Agent": REDDIT_USER_AGENT
        }

        resp = requests.post(
            REDDIT_OAUTH_URL,
            auth=auth,
            data=data,
            headers=headers,
            timeout=10,
        )

        resp.raise_for_status()

        token_data = resp.json()

        _cached_token = token_data["access_token"]

        expires_in = int(token_data.get("expires_in", 3600))

        # Refresh 60 seconds before expiration.
        _token_expiry = time.time() + max(0, expires_in - 60)

        return _cached_token


def _get_api_headers() -> Dict[str, str]:
    """Build authenticated Reddit API headers."""

    token = _get_oauth_token()

    return {
        "Authorization": f"bearer {token}",
        "User-Agent": REDDIT_USER_AGENT,
    }


def _format_timestamp(timestamp: float) -> str:
    """Convert Unix timestamp into readable UTC time."""

    return time.strftime(
        "%Y-%m-%d %H:%M:%S UTC",
        time.gmtime(timestamp or 0),
    )


# ============================================================
# REDDIT SEARCH
# ============================================================

def search_reddit(
    query: str,
    subreddit: str = "all",
    sort: str = "relevance",
    time_filter: str = "week",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Search Reddit posts using the official OAuth API.

    Returns post information including post_id,
    title, subreddit, author, score, URL and snippet.
    """

    subreddit = re.sub(
        r"^/?r/",
        "",
        subreddit.strip(),
        flags=re.IGNORECASE,
    ).strip("/")

    if not subreddit:
        subreddit = "all"

    limit = max(1, min(limit, 25))

    try:
        headers = _get_api_headers()

    except Exception as e:
        return [{
            "error": f"Reddit OAuth authentication failed: {str(e)}"
        }]

    url = f"{REDDIT_API_BASE}/r/{subreddit}/search"

    params = {
        "q": query,
        "restrict_sr": "0" if subreddit.lower() == "all" else "1",
        "sort": sort,
        "t": time_filter,
        "limit": limit,
        "raw_json": "1",
    }

    try:
        resp = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10,
        )

        resp.raise_for_status()

        children = (
            resp.json()
            .get("data", {})
            .get("children", [])
        )

    except Exception as e:
        return [{
            "error": f"Failed to search Reddit: {str(e)}"
        }]

    results = []

    for child in children:
        post = child.get("data", {})

        post_id = post.get("id", "")
        permalink = post.get("permalink", "")

        selftext = post.get("selftext", "").strip()

        if not selftext and post.get("url"):
            selftext = f"[External Link: {post.get('url')}]"

        results.append({
            "id": post_id,
            "post_id": post_id,
            "fullname": post.get("name", f"t3_{post_id}"),

            "title": post.get("title", "No Title"),
            "subreddit": post.get(
                "subreddit_name_prefixed",
                f"r/{subreddit}",
            ),

            "author": post.get("author", "unknown"),
            "score": post.get("score", 0),
            "num_comments": post.get("num_comments", 0),

            "url": f"https://www.reddit.com{permalink}",
            "permalink": f"https://www.reddit.com{permalink}",
            "link_url": post.get("url", ""),

            "published": _format_timestamp(
                post.get("created_utc", 0)
            ),

            "snippet": (
                selftext[:500] + "..."
                if len(selftext) > 500
                else selftext
            ),
        })

    return results


# ============================================================
# REDDIT COMMENT FETCHER
# ============================================================

def fetch_reddit_comments(
    post_id: str,
    sort: str = "top",
    limit: int = 50,
    depth: int = 5,
) -> Dict[str, Any]:
    """
    Fetch comments and replies for a Reddit post.

    Args:
        post_id:
            Reddit post ID, such as 'abc123'.
            Also accepts the fullname 't3_abc123'.

        sort:
            Comment sorting:
            top, new, controversial, old,
            random, qa, confidence or live.

        limit:
            Maximum number of comments to request (1-100).

        depth:
            Maximum reply nesting depth (1-10).

    Returns:
        Dictionary containing flattened comments,
        comment count and information about additional
        comments represented by Reddit 'more' placeholders.
    """

    # Normalize post ID.
    post_id = post_id.strip()

    # Accept full Reddit post URLs.
    url_match = re.search(
        r"/comments/([A-Za-z0-9]+)",
        post_id,
    )

    if url_match:
        post_id = url_match.group(1)

    # Remove Reddit fullname prefix.
    if post_id.startswith("t3_"):
        post_id = post_id[3:]

    if not re.fullmatch(r"[A-Za-z0-9]+", post_id):
        return {
            "error": "Invalid Reddit post ID."
        }

    limit = max(1, min(limit, 100))
    depth = max(1, min(depth, 10))

    valid_sorts = {
        "confidence",
        "top",
        "new",
        "controversial",
        "old",
        "random",
        "qa",
        "live",
    }

    if sort not in valid_sorts:
        return {
            "error": (
                f"Invalid comment sort: {sort}. "
                f"Valid options: {', '.join(sorted(valid_sorts))}"
            )
        }

    try:
        headers = _get_api_headers()

    except Exception as e:
        return {
            "error": f"Reddit OAuth authentication failed: {str(e)}"
        }

    url = f"{REDDIT_API_BASE}/comments/{post_id}"

    params = {
        "sort": sort,
        "limit": limit,
        "depth": depth,
        "raw_json": "1",
    }

    try:
        resp = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15,
        )

        resp.raise_for_status()

        payload = resp.json()

        if not isinstance(payload, list) or len(payload) < 2:
            return {
                "error": "Unexpected Reddit comments API response.",
                "post_id": post_id,
            }

        comment_children = (
            payload[1]
            .get("data", {})
            .get("children", [])
        )

    except Exception as e:
        return {
            "error": f"Failed to fetch Reddit comments: {str(e)}",
            "post_id": post_id,
        }

    comments: List[Dict[str, Any]] = []
    more_comment_ids: List[str] = []

    def extract_comments(
        children: List[Dict[str, Any]],
        current_depth: int = 0,
    ):
        """
        Recursively flatten Reddit's nested comment tree.
        """

        for child in children:

            if len(comments) >= limit:
                return

            kind = child.get("kind")
            data = child.get("data", {})

            # Reddit uses 'more' objects for omitted comments.
            if kind == "more":

                more_comment_ids.extend(
                    data.get("children", [])
                )

                continue

            if kind != "t1":
                continue

            comment_id = data.get("id", "")
            permalink = data.get("permalink", "")

            comment = {
                "id": comment_id,
                "fullname": data.get(
                    "name",
                    f"t1_{comment_id}",
                ),

                "body": data.get("body", ""),

                "author": data.get("author", "unknown"),
                "subreddit": data.get("subreddit_name_prefixed", ""),

                "score": data.get("score", 0),

                "published": _format_timestamp(
                    data.get("created_utc", 0)
                ),

                "url": (
                    f"https://www.reddit.com{permalink}"
                    if permalink
                    else ""
                ),

                "post_id": post_id,

                "parent_id": data.get("parent_id", ""),
                "depth": current_depth,

                "is_submitter": data.get("is_submitter", False),
                "edited": data.get("edited", False),
            }

            comments.append(comment)

            # Extract nested replies.
            replies = data.get("replies")

            if isinstance(replies, dict):
                reply_children = (
                    replies
                    .get("data", {})
                    .get("children", [])
                )

                if reply_children:
                    extract_comments(
                        reply_children,
                        current_depth + 1,
                    )

    extract_comments(comment_children)

    # Remove duplicate IDs from MoreComments placeholders.
    more_comment_ids = list(dict.fromkeys(more_comment_ids))

    return {
        "post_id": post_id,
        "comment_count": len(comments),

        "more_comments_available": bool(more_comment_ids),
        "more_comment_ids": more_comment_ids,

        "sort": sort,
        "comments": comments,
    }
