from pathlib import Path
from google.adk.agents import Agent

from ..tools.writing_tools import count_words, check_seo_lengths
from ..model_config import get_model


SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "writing.md"
SKILL = SKILL_PATH.read_text(encoding="utf-8")

writer = Agent(
    name="writer",
    model=get_model(),
    # model="gemini-3.5-flash-lite",
    description="Writes content using research findings.",
    instruction=f"""
    You are the writing specialist.

    Follow these skill instructions:
    {SKILL}

    Use the research findings provided by the coordinator.
    Write clear, accurate, well-structured content.
    Never invent facts or citations.
    """,
    tools=[count_words, check_seo_lengths]
)
