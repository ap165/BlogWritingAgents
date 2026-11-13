import requests, os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("CRAWL_4_WEB_KEY")

def load_web_page(url: str) -> dict:
    """Fetch a public web page"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        'Content-Type': 'application/json',
    }

    json_data = {
        'url': url,
        'f': 'fit',
        'q': None,
        'c': '0',
    }

    response = requests.post('https://crawl4ai.quietspace.world/md', headers=headers, json=json_data)
    return response.json()
