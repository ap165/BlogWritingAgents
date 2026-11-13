from pathlib import Path

from google.adk.agents import Agent

from ..model_config import get_model
from ..tools.web_search import web_search
from ..tools.writing_tools import check_seo_lengths
from ..tools.run_files import write_run_file, read_run_file


SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "seo.md"
)

SKILL = SKILL_PATH.read_text(encoding="utf-8")


seo_expert = Agent(
    name="seo_expert",
    model=get_model(),
    description="Researches search intent, keywords, SERPs, and prepares SEO briefs for blog articles.",
    instruction=f"""
    You are the SEO expert of an autonomous multi-niche blogging platform.

    Follow the instructions and methodologies defined in your skill:

    {SKILL}

    Analyze the provided topic, editorial brief, and research package.

    Perform SEO research and prepare a structured SEO brief
    for the Writer agent.

    Do not write the actual blog article.

    Use available tools when necessary.
    Never fabricate keyword metrics, search volumes, or SEO findings.

    Save the completed SEO brief using write_run_file
    when required by the workflow.
    """,
    tools=[
        web_search,
        check_seo_lengths,
        write_run_file,
        read_run_file,
    ]
)