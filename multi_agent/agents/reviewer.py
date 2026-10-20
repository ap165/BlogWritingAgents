from pathlib import Path
from google.adk.agents import Agent
# from google.adk.tools import google_search
from ..tools.review_tools import readability_score, similarity_check, check_links
from ..tools.writing_tools import check_seo_lengths
from ..model_config import get_model
from ..tools.google_search import web_search


SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "reviewing.md"
SKILL = SKILL_PATH.read_text(encoding="utf-8")

reviewer = Agent(
    name="reviewer",
    model=get_model(),
    # model="gemini-3.1-flash-lite",
    description="Reviews drafts for accuracy and quality.",
    instruction=f"""
    You are the quality reviewer.

    Follow these skill instructions:
    {SKILL}

    Review the draft and research findings.
    Identify factual errors, unsupported claims, and unclear writing.
    Return specific corrections and an approval status.
    Do not claim that facts were verified unless evidence supports it.
    """,
    tools=[web_search, readability_score, similarity_check, check_links, check_seo_lengths]
)
