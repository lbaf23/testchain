from utils import extract_test_cases, extract_first_block
from typing import List, Tuple
from code_models import ModelBase
import logging
from utils import execute_get_output, make_assert
from .python_inter import PyInterpreter


class CalculatorAgent:
    function_signature = '[Function Signature and Docstring]:'
    test_input = '[Test Input]:'
    thought = '[Thought]:'
    code = '[Code]:'
    observation = '[Observation]:'
    test_case = '[Test Case]:'

    system_prompt = f'''\
You are an expert Python programmer.
You will be given a function signature and docstring, along with a test input to the function.
Your task is to predict the test output corresponding to this test input and write a complete test case, which is represented by an assert statement.
You need to break the problem down into a series of steps, and for complex steps, you need to write Python program snippets to help with reasoning and calculations.

Use the following format:
{function_signature}
The function signature and docstring.
{test_input}
A test input for the function.
{thought}
You should always think about what to do.
{code}
The Python code snippet you want to execute.
{observation}
The execution results of the Python code snippet.
... (this {thought}/{code}/{observation} can repeat N times)
{thought}
I now know the final answer.
{test_case}
A single line of assert statement, put it in a Python code block.

Begin!
'''

    final_prompt = 'Please write the test case now.'
    go_on_prompt = 'Good job! Please go on.'

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

{test_input}
```text
input: [1, 3, 2, 5]
```

{thought}
To find the median of the given array, I should first sort the array. I will write Python code to sort it.
{code}
```python
arr = [1, 3, 2, 5]
arr = sorted(arr)
print(arr)
```

{observation}
[1, 2, 3, 5]

{thought}
I should then verify whether the length of the array is even or odd. I will count the length of the array with `len()` function.
{code}
```python
len(arr) % 2 == 0
```

{observation}
Out[1]: True

{thought}
The length of the array is even, so the median should be the average of the two middle numbers.

{observation}
<{go_on_prompt}>

{thought}
I will write Python code to calculate the average of the two middle numbers.
{code}
```python
median = float(arr[int(len(arr)/2)] + arr[int(len(arr)/2 - 1)]) / 2
print(median)
```

{observation}
2.5

{thought}
I now know the final answer.
{test_case}
```python
assert find_the_median([1, 3, 2, 5]) == 2.5
```

END OF EXAMPLES.
'''

    def __init__(
            self,
            model: ModelBase,
            py_inter: PyInterpreter = None,
    ) -> None:
        self.model = model
        self.py_inter = py_inter

    def format_output(self, output: str) -> Tuple[str, str, str]:
        if output.__contains__(self.thought):
            output = output[output.index(self.thought) + len(self.thought):].strip()

        code = ''
        thought = output
        test_case = ''
        if output.__contains__(self.code):
            thought = thought[: thought.index(self.code)].strip()
            code = output[output.index(self.code) + len(self.code):].strip()
            return 'code', thought, code
        elif output.__contains__(self.test_case):
            thought = thought[: thought.index(self.test_case)].strip()
            test_case = output[output.index(self.test_case) + len(self.test_case):].strip()
            return 'test_case', thought, test_case
        else:
            return 'error', thought, ''

    def make_message(self, thought: str, code: str = '') -> str:
        if code == '':
            return f'''\
{self.thought}
{thought}
'''
        else:
            return f'''\
{self.thought}
{thought}
{self.code}
```python
{code}
```
'''

    def generate(
            self,
            function_def: str,
            input: str,
            prompt_type: str,
            max_tokens: int = 512,
            temperature: float = 0.2,
            max_iterations: int = 5
    ) -> str:
        logging.info('=' * 20 + 'input' + '=' * 20)
        logging.info(input)

        if prompt_type == 'py_inter':
            test_case = self.generate_with_py_inter(
                function_def=function_def,
                input=input,
                max_tokens=max_tokens,
                temperature=temperature,
                max_iterations=max_iterations
            )
        elif prompt_type == 'directly':
            test_case = self.generate_directly(
                function_def=function_def,
                input=input,
                temperature=temperature
            )
        else:
            raise NotImplementedError

        return test_case

    def generate_with_py_inter(
            self,
            function_def: str,
            input: str,
            max_tokens: int = 512,
            temperature: float = 0.2,
            max_iterations: int = 5
    ) -> str:
        """
        Generate with interactive py interpreter
        Args:
            function_def (str): function signature and docstring
            input (str):
            max_tokens (int): default to 512
            temperature (float):
            max_iterations (int): default to 10
        Returns:
            (str): assert ...
        """

        stop_strs = [f'\n{self.observation}', f'{self.observation}\n', self.observation]

        system_prompt = self.system_prompt
        user_prompt = f'''\
{self.few_shot_prompt}

{self.function_signature}
```python
{function_def.strip()}
```
{self.test_input}
```text
input: {input}
```
'''
        messages = [
            {'role': 'system', 'content': system_prompt}
        ]

        logging.info('-' * 20 + 'calculator agent [system]' + '-' * 20)
        logging.info(system_prompt)

        i = 0
        test_cases = ''
        while i < max_iterations:
            messages.append({
                'role': 'user',
                'content': user_prompt
            })

            logging.info('-' * 20 + 'calculator agent [user]' + '-' * 20)
            logging.info(messages[-1]['content'])

            output = self.model.generate_chat(
                messages=messages,
                max_tokens=max_tokens,
                stop_strs=stop_strs,
                temperature=temperature
            )

            logging.info('-' * 20 + 'calculator agent [assistant]' + '-' * 20)
            logging.info(output)
            logging.info('-' * 100)

            call, thought, content = self.format_output(output)
            if call == 'code':
                code = extract_first_block(content)

                messages.append({
                    'role': 'assistant',
                    'content': f'''\
{self.thought}
{thought}
{self.code}
```python
{code}
```
'''
                })
                obs = ''
                if code != '':
                    obs = self.py_inter.run_cell(code)
                    user_prompt = f'''\
{self.observation}
{obs}
'''
                else:
                    user_prompt = f'''\
{self.observation}
<{self.go_on_prompt}>
'''
            elif call == 'test_case':
                user_prompt = ''
                test_cases = content
                break
            else:
                messages.append({
                    'role': 'assistant',
                    'content': f'''\
{self.thought}
{thought}
'''
                })
                user_prompt = f'''\
{self.observation}
<{self.go_on_prompt}>
'''
            i += 1

        # if failed to generate in 5 rounds, then generate the test case immediately
        if test_cases == '':
            if user_prompt.startswith(self.observation):
                user_prompt += f'''\
{self.thought}
{self.final_prompt}
{self.test_case}
'''
            else:
                user_prompt = f'''\
{self.thought}
{self.final_prompt}
{self.test_case}
'''

            messages.append({
                'role': 'user',
                'content': user_prompt
            })

            output = self.model.generate_chat(
                messages=messages,
                max_tokens=max_tokens,
                stop_strs=stop_strs,
                temperature=temperature
            )

            logging.info('-' * 20 + ' calculator agent [user]' + '-' * 20)
            logging.info(messages[-1]['content'])

            logging.info('-' * 20 + 'calculator agent [assistant]' + '-' * 20)
            logging.info(output)

            test_cases = output

        self.py_inter.clear()

        test_cases = test_cases.strip()
        ret = extract_test_cases(test_cases)
        if len(ret) == 0:
            ret = test_cases.strip().split('\n')

        logging.info('-' * 20 + 'calculator agent [test case]' + '-' * 20)
        logging.info(ret[0])

        return ret[0]

    def generate_directly_from_code(
            self,
            entry_point: str,
            input: str,
            code: str,
    ) -> str:
        """
        Calculate output directly with a generated code or directly predict
        """
        test_input = input

        if test_input.startswith('(') and test_input.endswith(')'):
            test_input = test_input[1:-1]

        test_output = execute_get_output(test_input, entry_point, code)
        return make_assert(test_input, test_output, entry_point)

    thought_and_test_case = '[Thought and Test Case]:'

    def generate_directly_reasoning(
            self,
            function_def: str,
            entry_point: str,
            input: str,
    ) -> str:
        system_prompt = 'You are a Python test programmer.'
        user_prompt = f'''\
You are provided with a function signature and docstring, along with a test input.
Your task is to predict the test output and write the test case statement corresponding to the test input.
You should first use 2-3 sentences to describe your thought, then you should write the test case with a single line of assert statement in a Python code block.

For example:

{self.function_signature}
```python
from typing import List

def find_the_median(arr: List[int]) -> float:
    """
    Given an unsorted array of integers `arr`, find the median of the array.
    The median is the middle value in an ordered list of numbers.
    If the length of the array is even, then the median is the average of the two middle numbers.
    """
```

{self.test_input}
```text
input: [1, 3, 2, 5]
```

{self.thought_and_test_case}
The middle number of the input array is 2 and 3, so the medium should be the average of the two numbers 2.5.
```python
assert find_the_median([1, 3, 2, 5]) == 2.5
```

End of examples.


{self.function_signature}
```python
{function_def}
```

{self.test_input}
```text
input: {input}
```

{self.thought_and_test_case}
'''
        output = self.model.generate_chat(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            stop_strs=[self.function_signature, self.test_input],
            max_tokens=512,
            temperature=0.2
        )

        logging.info('-' * 20 + 'calculator agent generate_directly_reasoning [system]' + '-' * 20)
        logging.info(system_prompt)
        logging.info('-' * 20 + 'calculator agent generate_directly_reasoning [user]' + '-' * 20)
        logging.info(user_prompt)
        logging.info('-' * 20 + 'calculator agent generate_directly_reasoning [assistant]' + '-' * 20)
        logging.info(output)

        test_output = extract_first_block(output, 'python')
        test_case = test_output.split('\n')[0]
        return test_case

    def generate_directly(
            self,
            function_def: str,
            entry_point: str,
            input: str,
    ) -> str:
        system_prompt = 'You are a Python test programmer.'
        user_prompt = f'''\
You are provided with a function signature and docstring, along with a test input.
Your task is to predict the test output and write the test case statement corresponding to the test input.
You should write the test case with a single line of assert statement in a Python code block, without any other content.

For example:

{self.function_signature}
```python
from typing import List

def find_the_median(arr: List[int]) -> float:
    """
    Given an unsorted array of integers `arr`, find the median of the array.
    The median is the middle value in an ordered list of numbers.
    If the length of the array is even, then the median is the average of the two middle numbers.
    """
```

{self.test_input}
```text
input: [1, 3, 2, 5]
```

{self.test_case}
```python
assert find_the_median([1, 3, 2, 5]) == 2.5
```

End of examples.


{self.function_signature}
```python
{function_def}
```

{self.test_input}
```text
input: {input}
```

{self.test_case}
'''
        output = self.model.generate_chat(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            stop_strs=[self.function_signature, self.test_input],
            max_tokens=256,
            temperature=0.2
        )

        logging.info('-' * 20 + 'calculator agent generate_directly [system]' + '-' * 20)
        logging.info(system_prompt)
        logging.info('-' * 20 + 'calculator agent generate_directly [user]' + '-' * 20)
        logging.info(user_prompt)
        logging.info('-' * 20 + 'calculator agent generate_directly [assistant]' + '-' * 20)
        logging.info(output)

        test_output = extract_first_block(output, 'python')
        test_case = test_output.split('\n')[0]
        return test_case
