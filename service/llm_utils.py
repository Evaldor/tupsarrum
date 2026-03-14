import logging
from typing import List
from langchain_openai import ChatOpenAI
from openai import OpenAI
import httpx
from config import LLM_BASE_URL, LLM_API_KEY, LLM_PROVIDER
from conversation_state import Message


logger = logging.getLogger()

class LLMManager:

    def __init__(self):
        # =============================
        # 🔧 Настройка LLM (языковые модели)
        # =============================
        if LLM_PROVIDER == "deepseek":
            self.client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        else:
            logger.error(f"Cant handle llm_provider")

    def call(self, dialog: List[Message], temperature: float = 1.0, model: str = "-", give_json: bool = False): 
        try:
            if give_json:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=dialog,
                    stream=False,
                    temperature=temperature,
                    response_format={
                        'type': 'json_object'
                    }
                )
            else:
                response = self.llm_general.chat.completions.create(
                    model=model,
                    messages=dialog,
                    stream=False,
                    temperature=temperature
                )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in llm api request: {e}")
            return "Error"
