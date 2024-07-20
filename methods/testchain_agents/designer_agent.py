from utils import extract_test_inputs
from typing import List
from code_models import ModelBase
import logging


class DesignerAgent:
    system_prompt = '''\
You are a Python tester. Your task is to generate a comprehensive set of test inputs for the given function signature and problem description. 
The generated test inputs should cover all requirements, edge cases, exceptional scenarios, and satisfy the constraints specified in the problem description. 
Write each test input in a single line and start with a `input:` prefix, put your answer in a text block, such as ```text
# test inputs here
```'''

    function_signature = '[FUNCTION SIGNATURE]:'
    test_inputs = '[TEST INPUTS]:'

    few_shot_prompt = f'''\
EXAMPLES:

{function_signature}
```python
from typing import List

def find_the_median(arr: List[int]) -> float:
    """
    Given an unsorted array of integers `arr`, find the median of the array.
    The median is the middle value in an ordered list of numbers.
    If the length of the array is even, then the median is the average of the two middle numbers.
    """
```

{test_inputs}
```text
input: [3, 1, 2]
input: [1, 3, 2, 5]
input: [1]
input: [-1, -2, -3, 4, 5]
input: [4, 4, 4]
input: [-1, -2, -3, -4, -5, -6, -7, -8, -9]
```

END OF EXAMPLES.
'''

    def __init__(
            self,
            model: ModelBase,
    ) -> None:
        self.model = model

    def generate(
            self,
            function_def: str,
            max_tokens: int = 256,
            temperature: float = 0.2
    ) -> List[str]:
        system_prompt = self.system_prompt
        user_prompt = f'''\
{self.few_shot_prompt}

{self.function_signature}
```python
{function_def.strip()}
```

{self.test_inputs}'''
        messages = [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': user_prompt
            }
        ]

        logging.info('-' * 20 + 'designer agent [system]' + '-' * 20)
        logging.info(system_prompt)
        logging.info('-' * 20 + 'designer agent [user]' + '-' * 20)
        logging.info(user_prompt)

        output = self.model.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        logging.info('-' * 20 + 'designer agent [assistant]' + '-' * 20)
        logging.info(output)
        logging.info('-' * 50)

        return extract_test_inputs(output, 'input:')
