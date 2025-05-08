from utils import extract_test_inputs
from typing import List
from code_models import ModelBase
import logging


class DesignerAgent:
    function_signature = '[FUNCTION SIGNATURE]:'

    existing_test_inputs = '[EXISTING TEST INPUTS]:'
    additional_test_inputs = '[ADDITIONAL TEST INPUTS]:'
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
input: [-1, -2, -3, 3, 2, 1, 0]
input: [0, 0, 0]
input: [-1, 0, 0, 0]
input: [-1, -1, -1]
...
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
            max_tokens: int = 1024,
            temperature: float = 0.2,
    ) -> List[str]:
        system_prompt = '''\
You are a Python tester. Your task is to generate a comprehensive set of test inputs for the given function signature and problem description. 
The generated test inputs should cover all requirements, edge cases, exceptional scenarios, and satisfy the constraints specified in the problem description. 
Write each test input in a single line and start with a `input:` prefix, and write as many test inputs as possible. Put your answer in a text block, for example:
```text
# test inputs here
```'''

        user_prompt = f'''\
{self.few_shot_prompt}

{self.function_signature}
```python
{function_def.strip()}
```

{self.test_inputs}'''
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
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

        test_inputs = extract_test_inputs(output, 'input:')
        return test_inputs

    def generate_additional(
            self,
            function_def: str,
            existing: List[str],
            max_tokens: int = 1024,
            temperature: float = 0.2,
    ) -> List[str]:
        system_prompt = '''\
You are a Python tester. Your task is to generate a comprehensive set of test inputs for the given function signature and problem description.
The generated test inputs should cover all requirements, edge cases, exceptional scenarios, and satisfy the constraints specified in the problem description.
Write each test input in a single line and start with a `input:` prefix, and do not duplicating the existing test inputs. Put your answer in a text block, for example:
```text
# test inputs here
```'''
        existing = '\n'.join(['input: ' + e for e in existing]).strip()
        user_prompt = f'''\
{self.few_shot_prompt}

{self.function_signature}
```python
{function_def.strip()}
```

{self.existing_test_inputs}
```text
{existing}
```

{self.additional_test_inputs}'''
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
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

        test_inputs = extract_test_inputs(output, 'input:')
        return test_inputs
