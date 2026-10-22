from google.adk.agents import Agent
from ..model_config import get_model

trendAnalyzer = Agent(
    name="trend_analyzer",
    model=get_model()
)