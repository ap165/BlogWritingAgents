from google.adk.agents import Agent
from ..model_config import get_model
from pathlib import Path
from ..tools.google_search import web_search
from ..tools.research_tools import load_web_page

skill_path = Path(__file__).parents[1] / "skills" / "trend_analysis.md"
skill = skill_path.read_text(encoding="utf-8")

trendAnalyzer = Agent(
    name="trend_analyzer",
    model=get_model(),
    description="Researches topics and provides evidence to the writer.",
        instruction= f"""
            You are the research specialist.
    
            Follow these skill instructions:
            {skill}
    
            Research the assigned topic and return useful findings,
            supporting sources where available, and an outline.
            Never invent sources.
        """,
        tools=[web_search, load_web_page]
)