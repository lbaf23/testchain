from typing import List, Dict, Union
from tenacity import retry, wait_random_exponential, stop_after_attempt
from openai import OpenAI
from .models import ModelBase


@retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(5))
def gpt_chat(
    client: OpenAI,
    model: str,
    messages: List[Dict],
    max_tokens: int = 1024,
    stop_strs: List[str] = [],
    temperature: float = 0.2,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.95,
        stop=stop_strs
    )
    return response.choices[0].message.content


class GPTChat(ModelBase):
    def __init__(self, model_name: str, **args):
        self.model_name = model_name
        self.client = OpenAI(**args)

    def generate_chat(self, messages: List[Dict], max_tokens: int = 1024, stop_strs: List[str] = [], temperature: float = 0.2) -> str:
        return gpt_chat(self.client, self.model_name, messages, max_tokens, stop_strs, temperature)
    
    def generate(self, prompt: str, max_tokens: int = 1024, stop_strs: List[str] = [], temperature: float = 0.2) -> str:
        completion = self.client.completions.create(
            model=self.model_name,
            prompt=prompt,
            stop=stop_strs,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95
        )
        return completion.choices[0].text


