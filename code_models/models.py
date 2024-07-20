from typing import List, Dict


class ModelBase():
    def __init__(self, name: str):
        self.name = name
        self.is_chat = False

    def __repr__(self) -> str:
        return f'{self.name}'

    def generate_chat(self, messages: List[Dict], max_tokens: int = 1024, stop_strs: List[str] = [], temperature: float = 0.2) -> str:
        raise NotImplementedError

    def generate(self, prompt: str, max_tokens: int = 1024, stop_strs: List[str] = [], temperature: float = 0.2) -> str:
        raise NotImplementedError
