from pathlib import Path
from google.adk.agents import Agent

from .researcher import researcher
from .writer import writer
from .reviewer import reviewer
from ..tools.publishing_tools import save_draft
# from ..model_config import get_model

skill_path = Path(__file__).parents[1] / "skills" / "coordinator.md"

Skill = skill_path.read_text(encoding='utf-8')


coordinator = Agent(
    name="coordinator",
    # model=get_model(),
    model="gemini-3.5-flash-lite",
    description="Coordinates research, writing, and quality review.",
    instruction= f"""
    You are the coordinator of a four-agent team.

    Your team consists of:
    1. researcher
    2. writer
    3. reviewer

    skill: {Skill}

    For every content creation task:

    1. Delegate research to researcher.
    2. Give the research findings to writer.
    3. Send the resulting draft and available evidence to reviewer.
    4. If the reviewer finds important issues, request a revision.
    5. Limit revisions to two attempts.
    6. Return the final draft and review status.

    Delegate tasks to the appropriate sub-agent.
    Do not claim a task is complete if a required stage failed.
    """,
    sub_agents=[researcher, writer, reviewer],
    tools=[save_draft]
)
