import requests

def web_search(query: str) -> dict:
    """
    Search Google using Bright Data's SERP API.

    Args:
        query: Search query.

    Returns:
        Search result in json format.
    """
    query = query.strip() if isinstance(query, str) else ""
    API_URL = f"https://search.quietspace.world/search?q={query}&format=json"
    data = requests.get(API_URL)
    return data.json()

print(web_search("doremon"))