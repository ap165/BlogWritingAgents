from pathlib import Path
from google.adk.agents import Agent

from ..tools.writing_tools import count_words, check_seo_lengths
from ..model_config import get_model
from ..tools.run_files import write_run_file, read_run_file


SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "writing.md"
SKILL = SKILL_PATH.read_text(encoding="utf-8")

## Tech, politics, finance and other news writer
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
    tools=[count_words, check_seo_lengths, write_run_file, read_run_file]
)


ENT_SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "ent_writing.md"
ENT_SKILL = SKILL_PATH.read_text(encoding="utf-8")

## entertainment(Anime, Movies, TV shows etc.) writer
entertainment_writer = Agent(
    name="entertainment_writer",
    model=get_model(),
    # model="gemini-3.5-flash-lite",
    description="Writes content using research findings.",
    instruction=f"""
    You are the entertainment(Anime, Movies, TV shows etc.) writing specialist.

    Follow these skill instructions:
    {ENT_SKILL}

    Use the research findings provided by the coordinator.
    Write clear, accurate, well-structured content.
    Never invent facts or citations.
    """,
    tools=[count_words, check_seo_lengths, write_run_file, read_run_file]
)


EDU_SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "edu_writing.md"
EDU_SKILL = SKILL_PATH.read_text(encoding="utf-8")

## educational writer
educational_writer = Agent(
    name="educational_writer",
    model=get_model(),
    # model="gemini-3.5-flash-lite",
    description="Writes content using research findings.",
    instruction=f"""
    You are the educational content writing specialist.

    Follow these skill instructions:
    {SKILL}

    Use the research findings provided by the coordinator.
    Write clear, accurate, well-structured content.
    Never invent facts or citations.
    """,
    tools=[count_words, check_seo_lengths, write_run_file, read_run_file]
)