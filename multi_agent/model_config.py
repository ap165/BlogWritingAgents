from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
import os

load_dotenv()

model = "nvidia/nemotron-3-ultra-550b-a55b:free"
# model = "minimax/minimax-m3.1-flash:free"

def get_model():
    return LiteLlm(
        model= f"openrouter/{model}",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )