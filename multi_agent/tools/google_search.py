
import os
from pathlib import Path

from dotenv import load_dotenv
from tavily import TavilyClient

# Load multi_agent/.env
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def web_search(query: str, max_results: int = 5) -> dict:
    """
    Search the live web for information relevant to a research query.

    Args:
        query: The topic, question, or keywords to search for.
        max_results: Maximum number of results to return, from 1 to 5.

    Returns:
        Search results containing titles, URLs, snippets, and relevance scores.
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "TAVILY_API_KEY is missing from multi_agent/.env.",
        }

    if not query or not query.strip():
        return {
            "status": "error",
            "message": "Search query cannot be empty.",
        }

    try:
        client = TavilyClient(api_key=api_key)

        response = client.search(
            query=query.strip(),
            search_depth="basic",
            max_results=max(1, min(max_results, 5)),
            include_answer=False,
            include_raw_content=False,
        )

        results = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "score": item.get("score", 0),
            }
            for item in response.get("results", [])
        ]

        return {
            "status": "success",
            "query": query,
            "results": results,
            "result_count": len(results),
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": f"Web search failed: {str(exc)[:300]}",
        }
