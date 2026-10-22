import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

API_URL = "https://api.brightdata.com/request"
RETRY_STATUS = {429, 500, 502, 503, 504}


def _extract_payload(data) -> dict:
    """Return the parsed SERP dict.

    Bright Data can return the parsed result directly ({"organic": [...]}),
    or wrapped like {"status_code": 200, "headers": {...}, "body": "<json string>"}.
    Your old code only handled the first form, so the wrapped form gave 0 results.
    """
    if isinstance(data, dict) and "organic" in data:
        return data
    if isinstance(data, dict) and "body" in data:
        body = data["body"]
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except ValueError:
                return {}
        if isinstance(body, dict):
            return body
    return {}


def web_search(query: str, max_results: int = 5) -> dict:
    """
    Search Google using Bright Data's SERP API.

    Args:
        query: Search query.
        max_results: Maximum number of organic results, from 1 to 10.

    Returns:
        A dict with status "success", "no_results" or "error".
        On success it contains results with title, url, snippet and rank.
    """
    query = query.strip() if isinstance(query, str) else ""
    if not query:
        return {"status": "error", "message": "Search query cannot be empty."}

    api_key = os.getenv("BRIGHTDATA_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "BRIGHTDATA_API_KEY is missing. Put it in multi_agent/.env.",
        }

    try:
        max_results = max(1, min(int(max_results), 10))
    except (ValueError, TypeError):
        max_results = 5

    read_timeout = int(os.getenv("BRIGHTDATA_TIMEOUT", "75"))
    attempts = max(1, int(os.getenv("BRIGHTDATA_ATTEMPTS", "2")))
    debug = os.getenv("BRIGHTDATA_DEBUG") == "1"

    google_url = "https://www.google.com/search?" + urlencode({
        "q": query,
        "hl": os.getenv("BRIGHTDATA_GOOGLE_LANGUAGE", "en"),
        "gl": os.getenv("BRIGHTDATA_GOOGLE_COUNTRY", "in"),
    })

    payload = {
        "zone": os.getenv("BRIGHTDATA_SERP_ZONE", "serp_api1"),
        "url": google_url,
        "format": "json",
        "data_format": "parsed_light",
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = None
    last_message = "Unknown error."

    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(
                API_URL, headers=headers, json=payload, timeout=(10, read_timeout)
            )
            if response.status_code in RETRY_STATUS and attempt < attempts:
                last_message = f"Bright Data returned HTTP {response.status_code}."
                time.sleep(2 * attempt)
                continue
            response.raise_for_status()
            data = response.json()
            break

        except requests.exceptions.Timeout:
            last_message = f"Search timed out after {read_timeout}s."
        except requests.exceptions.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else None
            hint = ""
            if code in (401, 403):
                hint = " Check the API key and that the zone name is correct and active."
            elif code in (400, 422):
                hint = " Check the zone name and request settings in the Bright Data dashboard."
            return {"status": "error", "message": f"Bright Data returned HTTP {code}.{hint}"}
        except (requests.exceptions.RequestException, ValueError) as exc:
            last_message = f"Search failed: {type(exc).__name__}."

        if attempt < attempts:
            time.sleep(2 * attempt)

    if data is None:
        return {"status": "error", "message": last_message}

    # The wrapped form carries the real HTTP status of the Google request.
    if isinstance(data, dict) and data.get("status_code") not in (None, 200):
        return {
            "status": "error",
            "message": f"Google request returned status {data.get('status_code')}.",
        }

    serp = _extract_payload(data)
    results = []
    for item in serp.get("organic", []) or []:
        url = item.get("link") or item.get("url")
        if not url:
            continue
        results.append({
            "title": item.get("title", ""),
            "url": url,
            "snippet": item.get("description") or item.get("snippet") or "",
            "rank": item.get("rank") or item.get("global_rank"),
        })
        if len(results) >= max_results:
            break

    if not results:
        out = {
            "status": "no_results",
            "query": query,
            "results": [],
            "result_count": 0,
            "message": "The request worked but no organic results were found or parsed.",
        }
        if debug:
            out["debug_top_level_keys"] = list(data.keys()) if isinstance(data, dict) else str(type(data))
            out["debug_raw_preview"] = json.dumps(data, default=str)[:800]
        return out

    return {
        "status": "success",
        "query": query,
        "results": results,
        "result_count": len(results),
    }


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "pizza"
    print(json.dumps(web_search(q), indent=2, ensure_ascii=False))