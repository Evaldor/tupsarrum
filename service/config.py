import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'placeholder_token')
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'placeholder_url')
LLM_API_KEY = os.getenv('LLM_API_KEY', '-')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'deepseek')
