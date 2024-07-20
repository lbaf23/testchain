from utils import extract_test_cases
from typing import List
from code_models import ModelBase
import logging


class TestAgent:
    system_prompt = '''\
You are a Python tester. Your task is to generate a comprehensive set of test cases for the given function signature and problem description. 
The generated test cases should cover all requirements, edge cases, exceptional scenarios, and satisfy the constraints specified in the problem description. 
Write each test case with a single line of assert statement, and put your answer in a Python code block.'''

    function_signature = '[FUNCTION SIGNATURE]:'
    thought = '[THOUGHT]:'
    test_cases = '[TEST CASES]:'

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
# Test with an odd length array
assert find_the_median([3, 1, 2]) == 2

# Test with an even length array
assert find_the_median([1, 3, 2, 5]) == 2.5

# Test with an array only contain a single element
assert find_the_median([1]) == 1

# Test with an array containing both positive and negative numbers
assert find_the_median([-1, -2, -3, 4, 5]) == -1

# Test with an arrays containing the same elements
assert find_the_median([4, 4, 4]) == 4

# Test with an array that only contain negative numbers
assert find_the_median([-1, -2, -3, -4, -5, -6, -7, -8, -9]) == -5

...
```

END OF EXAMPLES.
'''

    def __init__(
            self,
            model: ModelBase,
    ) -> None:
        self.model = model
    
    def generate_starcoder2(
            self,
            function_def: str,
            prompt_type: str = '0-shot',
            max_tokens: int = 512,
            temperature: float = 0.2
    ) -> List[str]:
        if prompt_type.startswith('0-shot'):
            prompt = f'''\
{self.system_prompt}
```python
{function_def.strip()}
```

### Test Cases
'''
        elif prompt_type.startswith('1-shot'):
            prompt = f'''\
{self.system_prompt}

### Function Signature
```python
from typing import List

def find_the_median(arr: List[int]) -> float:
    """
    Given an unsorted array of integers `arr`, find the median of the array.
    The median is the middle value in an ordered list of numbers.
    If the length of the array is even, then the median is the average of the two middle numbers.
    """
```

### Test Cases
```python
# Test with an odd length array
assert find_the_median([3, 1, 2]) == 2

# Test with an even length array
assert find_the_median([1, 3, 2, 5]) == 2.5

# Test with an array only contain a single element
assert find_the_median([1]) == 1

# Test with an array containing both positive and negative numbers
assert find_the_median([-1, -2, -3, 4, 5]) == -1

# Test with an arrays containing the same elements
assert find_the_median([4, 4, 4]) == 4

# Test with an array that only contain negative numbers
assert find_the_median([-1, -2, -3, -4, -5, -6, -7, -8, -9]) == -5

...
```

### Function Signature
```python
{function_def.strip()}
```

### Test Cases
'''
        else:
            raise NotImplementedError

        logging.info('-' * 20 + 'test agent [prompt]' + '-' * 20)
        logging.info(prompt)

        output = self.model.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

        logging.info('-' * 20 + 'test generator [output]' + '-' * 20)
        logging.info(output)
        logging.info('-' * 50)

        return extract_test_cases(output)


    def generate(
            self,
            function_def: str,
            prompt_type: str = '0-shot',
            max_tokens: int = 512,
            temperature: float = 0.2
    ) -> List[str]:
        if prompt_type.__contains__('starcoder2'):
            return self.generate_starcoder2(
                function_def,
                prompt_type,
                max_tokens,
                temperature
            )

        system_prompt = self.system_prompt
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
        elif prompt_type == 'cot':
            user_prompt = f'''\
{self.function_signature}
```python
{function_def.strip()}
```

{self.thought}
I'll consider all the scenarios. Let's think step by step:'''
        else:
            raise NotImplementedError

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

        return extract_test_cases(output)
