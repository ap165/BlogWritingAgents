from pathlib import Path
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .researcher import researcher
from .writer import writer
from .reviewer import reviewer
# from ..tools.publishing_tools import save_draft
from ..tools.run_files import save_final_draft, start_run
from ..model_config import get_model

skill_path = Path(__file__).parents[1] / "skills" / "coordinator.md"
Skill = skill_path.read_text(encoding="utf-8")

coordinator = Agent(
    name="coordinator",
    model=get_model(),
    description="Coordinates research, writing, and quality review.",
    instruction=f"""
        You are the coordinator of a multi-agent blog-writing system.

        Your tools are: start_run, researcher, writer, reviewer, save_final_draft.
        The specialists are tools. Each one returns a short status line to you,
        and you decide the next step. Content travels in files, never through you.

        Follow the coordinator skill exactly:

        {Skill}

        Always call start_run first. After each tool returns, go straight to
        the next step. Do not write a final answer until the run has ended.
        Never invent results.
    """,
    # sub_agents=[
    #     researcher,writer,reviewer
    # ],
    tools=[
        AgentTool(agent=researcher),
        AgentTool(agent=writer),
        AgentTool(agent=reviewer),
        save_final_draft,
        start_run
    ],
)