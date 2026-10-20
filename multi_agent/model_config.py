from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
import os

load_dotenv()

def get_model():
    return LiteLlm(
        model="nvidia_nim/deepseek-ai/deepseek-v4.1-flash",
        api_key=os.getenv("NVIDIA_NIM_API_KEY"),
    )