from pathlib import Path
from google.adk.agents import Agent
# from google.adk.tools import google_search

from ..tools.google_search import web_search
from ..tools.research_tools import load_web_page
from ..model_config import get_model


skill_path = Path(__file__).parents[1] / "skills" / "research.md"

Skill = skill_path.read_text(encoding='utf-8')

researcher = Agent(
    name="researcher",
    # model="gemini-3.5-flash-lite",
    model=get_model(),
    description="Researches topics and provides evidence to the writer.",
    instruction= f"""
        You are the research specialist.

        Follow these skill instructions:
        {Skill}

        Research the assigned topic and return useful findings,
        supporting sources where available, and an outline.
        Never invent sources.
    """,
    tools=[web_search, load_web_page]
)