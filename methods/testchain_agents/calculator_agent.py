from utils import extract_test_cases, extract_first_block
from typing import List, Tuple
from code_models import ModelBase
import logging
from .python_inter import PyInterpreter


class CalculatorAgent:
    function_signature = '[FUNCTION SIGNATURE]:'
    test_input = '[TEST INPUT]:'
    thought = '[THOUGHT]:'
    code = '[CODE]:'
    observation = '[OBSERVATION]:'
    test_case = '[TEST CASE]:'


    system_prompt = f'''\
You are a Python tester. Your task is to calculate the test output and write the test case statement corresponding to the test input for the function given the definition and docstring. Write each test case with a single line of assert statement. 
You have access to a Python interpreter, which allows you to execute any Python code snippet that assist in calculating the test output. Do not write the implementation of the target function directly.

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
    
    final_prompt = 'I now know the final answer.'
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
            model: ModelBase
    ) -> None:
        self.model = model

    def format_output(self, output: str) -> Tuple[str, str, str]:
        if output.__contains__(self.thought):
            output = output[output.index(self.thought) + len(self.thought) : ].strip()

        code = ''
        thought = output
        test_case = ''
        if output.__contains__(self.code):
            thought = thought[ : thought.index(self.code)].strip()
            code = output[output.index(self.code) + len(self.code) : ].strip()
            return 'code', thought, code
        elif output.__contains__(self.test_case):
            thought = thought[ : thought.index(self.test_case)].strip()
            test_case = output[output.index(self.test_case) + len(self.test_case) : ].strip()
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
        logging.info('=' * 50 + 'input' + '=' * 50)
        logging.info(input)

        if prompt_type == 'py_inter':
            test_case = self.generate_with_py_inter(
                function_def=function_def,
                input=input,
                max_tokens=max_tokens,
                temperature=temperature,
                max_iterations=max_iterations
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
        py_interpreter = PyInterpreter()
        stop_strs = [f'\n{self.observation}']

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
            {
                'role': 'system',
                'content': system_prompt
            }
        ]

        logging.info('-' * 50 + 'calculator agent [system]' + '-' * 50)
        logging.info(system_prompt)

        i = 0
        test_cases = ''
        while i < max_iterations:
            messages.append({
                'role': 'user',
                'content': user_prompt
            })
            
            logging.info('=' * 50 + 'calculator agent' + '=' * 50)
            logging.info('------' + 'assistant' + '------')
            logging.info(messages[-2]['content'])
            logging.info('------' + 'user' + '------')
            logging.info(messages[-1]['content'])
            logging.info('=' * 100)

            output = self.model.generate_chat(
                messages=messages,
                max_tokens=max_tokens,
                stop_strs=stop_strs,
                temperature=temperature
            )

            logging.info('-' * 50 + 'calculator agent [output]' + '-' * 50)
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
                    obs = py_interpreter.run_cell(code)
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

            logging.info('=' * 50 + 'calculator agent' + '=' * 50)
            logging.info('------' + 'assistant' + '------')
            logging.info(messages[-2]['content'])
            logging.info('------' + 'user' + '------')
            logging.info(messages[-1]['content'])
            logging.info('=' * 100)


            logging.info('-' * 50 + 'calculator agent [assistant]' + '-' * 50)
            logging.info(output)
            logging.info('-' * 100)

            test_cases = output

        py_interpreter.create()

        test_cases = extract_test_cases(test_cases)

        if len(test_cases) > 0:
            return test_cases[0]
        else:
            return ''

