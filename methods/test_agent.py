from utils import extract_test_cases
from typing import List
from code_models import ModelBase
import logging


class TestAgent:

    function_signature = '[FUNCTION SIGNATURE]:'
    thought = '[THOUGHT]:'
    test_cases = '[TEST CASES]:'
    existing_test_cases = '[EXISTING TEST CASES]:'
    additional_test_cases = '[ADDITIONAL TEST CASES]:'

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

{test_cases}
```python
assert find_the_median([3, 1, 2]) == 2
assert find_the_median([1, 3, 2, 5]) == 2.5
assert find_the_median([1]) == 1
assert find_the_median([-1, -2, -3, 4, 5]) == -1
assert find_the_median([4, 4, 4]) == 4
assert find_the_median([-1, -2, -3, -4, -5, -6, -7, -8, -9]) == -5
assert find_the_median([-1, -2, -3, 3, 2, 1, 0]) == 0
assert find_the_median([0, 0, 0]) == 0
assert find_the_median([-1, 0, 0, 0]) == 0
assert find_the_median([-1, -1, -1]) == -1
...
```

END OF EXAMPLES.
'''

    def __init__(
            self,
            model: ModelBase,
    ) -> None:
        self.model = model

    def generate_tests(
            self,
            function_def: str,
            prompt_type: str = '0-shot',
            max_tokens: int = 1024,
            temperature: float = 0.2,
    ) -> List[str]:

        system_prompt = '''\
You are a Python tester. Your task is to generate a comprehensive set of test cases for the given function signature and problem description. 
The generated test cases should cover all requirements, edge cases, exceptional scenarios, and satisfy the constraints specified in the problem description. 
Write each test case with a single line of assert statement, and write as many test cases as possible. Put your answer in a Python code block.'''

        if prompt_type == '0-shot':
            user_prompt = f'''\
{self.function_signature}
```python
{function_def.strip()}
```

{self.test_cases}'''
        elif prompt_type == '1-shot':
            user_prompt = f'''\
{self.few_shot_prompt}

{self.function_signature}
```python
{function_def.strip()}
```

{self.test_cases}'''
        else:
            raise NotImplementedError

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        logging.info('-' * 20 + 'test agent [system]' + '-' * 20)
        logging.info(system_prompt)
        logging.info('-' * 20 + 'test agent [user]' + '-' * 20)
        logging.info(user_prompt)

        output = self.model.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        logging.info('-' * 20 + 'test generator [assistant]' + '-' * 20)
        logging.info(output)
        logging.info('-' * 50)

        tests = extract_test_cases(output)
        return tests

    def generate_additional(
            self,
            function_def: str,
            existing: List[str],
            prompt_type: str = '0-shot',
            max_tokens: int = 1024,
            temperature: float = 0.2,
    ) -> List[str]:
        system_prompt = '''\
You are a Python tester. Your task is to generate a comprehensive set of test cases for the given function signature and problem description. 
The generated test cases should cover all requirements, edge cases, exceptional scenarios, and satisfy the constraints specified in the problem description. 
Write each test case with a single line of assert statement, and do not duplicating the existing test cases. Put your answer in a Python code block.'''

        existing = '\n'.join(existing)
        if prompt_type == '0-shot':
            user_prompt = f'''\
{self.function_signature}
```python
{function_def.strip()}
```

{self.existing_test_cases}
```python
{existing}
```

{self.additional_test_cases}'''
        elif prompt_type == '1-shot':
            user_prompt = f'''\
{self.few_shot_prompt}

{self.function_signature}
```python
{function_def.strip()}
```

{self.existing_test_cases}
```python
{existing}
```

{self.additional_test_cases}'''
        else:
            raise NotImplementedError

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        logging.info('-' * 20 + 'test agent [system]' + '-' * 20)
        logging.info(system_prompt)
        logging.info('-' * 20 + 'test agent [user]' + '-' * 20)
        logging.info(user_prompt)

        output = self.model.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        logging.info('-' * 20 + 'test generator [assistant]' + '-' * 20)
        logging.info(output)
        logging.info('-' * 50)

        tests = extract_test_cases(output)
        return tests

    def generate(
            self,
            function_def: str,
            existing_test_cases: List[str] = [],
            prompt_type: str = '0-shot',
            max_tokens: int = 1024,
            temperature: float = 0.2,
            tests_count: int = 10
    ) -> List[str]:
        tests = existing_test_cases

        gens = 0
        while len(tests) < tests_count:
            if len(tests) == 0:
                tests = self.generate_tests(
                    function_def=function_def,
                    prompt_type=prompt_type,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                tests += self.generate_additional(
                    function_def=function_def,
                    existing=tests,
                    prompt_type=prompt_type,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            gens += 1
            if gens > 10:
                break

        return tests
