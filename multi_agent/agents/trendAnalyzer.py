from google.adk.agents import Agent
from ..model_config import get_model
from pathlib import Path
from ..tools.web_search import web_search
from ..tools.web_crawler import load_web_page
from ..tools.get_google_trends import get_trends
from ..tools.google_news import search_news
from ..tools.search_reddit import search_reddit
from ..tools.other_rss import get_rss_feed


skill_path = Path(__file__).parents[1] / "skills" / "trend_analysis.md"
skill = skill_path.read_text(encoding="utf-8")

trendAnalyzer = Agent(
    name="trend_analyzer",
    model=get_model(),
    description="Discovers and ranks current trends across categories or specified niches, using reliable sources to explain momentum, relevance, and supporting evidence.",
    instruction= f"""
        You are an editorial trend-discovery specialist.

        Follow these skill instructions:
        {skill}

        Use `get_trends`, `get_rss_feed`, `search_news`, `search_reddit`, `web_search`, and `load_web_page` to discover and verify trending topics (defaulting to 20 across all categories if unspecified).

        Return write-ready pitches for blog articles, business case studies, news, or reviews (movies, TV, anime, games) with verified catalysts, community sentiment, a structured outline, and real source URLs. Never invent facts or sources.
    """,
    tools=[get_trends, get_rss_feed, search_news, search_reddit, web_search, load_web_page]
)