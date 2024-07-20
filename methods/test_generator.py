from utils import extract_test_cases
from typing import List
from code_models import ModelBase
import logging


class TestGenerator:
    def __init__(
            self,
            model: ModelBase,
    ) -> None:
        self.model = model

    def generate(
            self,
            function_def: str,
            prompt_type: str = 'codet',
            max_tokens: int = 512,
            temperature: float = 0.2
        ) -> List[str]:

        if prompt_type == 'codet':
            prompt = f'''\
{function_def.strip()}
    pass
assert'''
        else:
            raise NotImplementedError

        logging.info('-' * 20 + 'codellama [prompt]' + '-' * 20)
        logging.info(prompt)

        output = self.model.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

        logging.info('-' * 20 + 'codellama [output]' + '-' * 20)
        logging.info(output)
        logging.info('-' * 50)

        return extract_test_cases('assert' + output)
