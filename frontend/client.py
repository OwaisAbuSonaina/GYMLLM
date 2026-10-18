import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GOOGLE_API_KEY")

OPENAI_MODEL = "gpt-4.1-nano"
GEMINI_MODEL = "gemini-3.8-flash"
LLAMA_MODEL = "llama3.2"

openai_client = OpenAI()
gemini_client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=gemini_api_key)
llama_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

base_url = os.getenv("BACKEND_URL", "http://backend:8000")
GYMLLM_API_URL = f"{base_url}/GYMLLM"