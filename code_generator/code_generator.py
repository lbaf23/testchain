from code_models import ModelBase
from typing import List
import ast, black
import logging


def extract_blocks(content: str) -> List[str]:
    """
    extract all blocks content and return as a list
    """
    blocks = []
    if content.__contains__('```'):
        lines = content.strip().split('\n')
        i = 0
        while i < len(lines):
            while i < len(lines):
                if lines[i].strip().startswith('```'):
                    i += 1
                    break
                i += 1
            block = ''
            while i < len(lines):
                if lines[i].strip().startswith('```'):
                    i += 1
                    blocks.append(block.strip())
                    break
                block += lines[i] + '\n'
                i += 1
    return blocks


def strip_code(code: str) -> str:
    if code.__contains__('\nassert'):
        code = code[ : code.index('\nassert')].strip()
    return code


def format_code(code: str, lang: str = 'python') -> str:
    if lang == 'python':
        code = ast.parse(code)
        code = ast.unparse(code)
        code = black.format_str(code, mode=black.Mode(line_length=100000))
        code = code.strip()
        return code
    else:
        raise NotImplementedError


def extract_code(content: str, lang: str = 'python') -> str:
    """
    extract a program
    """
    code = content
    blocks = extract_blocks(content)
    if len(blocks) > 0:
        code = blocks[0]

    try:
        code = format_code(code, lang)
    except Exception:
        pass
    return code


class CodeGenerator:
    def __init__(
            self,
            model: ModelBase,
            lang: str = 'python'
        ) -> None:
        self.model = model
        self.lang = lang

    def generate(
            self,
            prompt: str,
            max_tokens: int = 1024,
            temperature: float = 0.8
    ) -> str:
        system_prompt = '''\
As a Python programmer, your task is to create full implementation for function given the signature and docstring. Use a Python code block to write your program.'''

        user_prompt = f'''\
### Function Signature and Docstring
```python
{prompt.strip()}
```

### Implementation
'''
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        logging.info('-'*50 + 'generate system' + '-'*50)
        logging.info(system_prompt)
        logging.info('-'*50 + 'generate user' + '-'*50)
        logging.info(user_prompt)

        output = self.model.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        logging.info('-'*50 + 'generate assistant' + '-'*50)
        logging.info(output)

        code = extract_code(output)
        code = strip_code(code)
        return code

    def generate_reflection(
            self,
            prompt: str,
            code: str,
            code_feedback: str,
            max_tokens: int = 256,
            temperature: float = 0.2
    ) -> str:
        assert code_feedback != ''

        system_prompt = 'As a Python programmer, you are given a function signature and docstring, and a program with its failed test case. Your task is to explain why the program is wrong in neural langauge, do not write any program.'
        user_prompt = f'''\
### Function Signature and Docstring
```python
{prompt}
```

### Program
```python
{code}
```

### Failed Test Case
{code_feedback}

### Reflection
'''
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        logging.info('-'*50 + 'generate_reflection system' + '-'*50)
        logging.info(system_prompt)
        logging.info('-'*50 + 'generate_reflection user' + '-'*50)
        logging.info(user_prompt)

        output = self.model.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        logging.info('-'*50 + 'generate_reflection assistant' + '-'*50)
        logging.info(output)

        return output

    def generate_reflexion_code(
            self,
            prompt: str,
            code: str,
            code_feedback: str,
            message: str,
            max_tokens: int = 1024,
            temperature: float = 0.2
    ) -> str:
        assert code_feedback != ''

        system_prompt = 'As a Python programmer, you are given a function signature and docstring, a program with its failed test case, and an explanation why the program is wrong. Your task is to write the corrected program. Use a Python code block to write your response.'
        user_prompt = f'''\
### Function Signature and Docstring
```python
{prompt}
```

### Program
```python
{code}
```

### Failed Test Case
{code_feedback}

### Reflection
{message}

### Improved Program
'''
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        logging.info('-'*50 + 'generate_reflexion_code system' + '-'*50)
        logging.info(system_prompt)
        logging.info('-'*50 + 'generate_reflexion_code user' + '-'*50)
        logging.info(user_prompt)

        output = self.model.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        logging.info('-'*50 + 'generate_reflexion_code assistant' + '-'*50)
        logging.info(output)

        code = extract_code(output)
        code = strip_code(code)
        return code

    def generate_reflection_with_history(
            self,
            prompt: str,
            code: str,
            history: str,
            code_feedback: str,
            history_feedback: str,
            max_tokens: int = 256,
            temperature: float = 0.2
    ) -> str:
        assert code_feedback != ''
        assert history_feedback != ''

        system_prompt = 'As a Python programmer, you are given a function signature and docstring, and a program with its failed test case. The user has made some modifications, but the program is still wrong. Your task is to explain why the program is still wrong in neural language, do not write any program.'
        user_prompt = f'''\
### Function Signature and Docstring
```python
{prompt}
```

### Program
```python
{history}
```

### Failed Test Case
{history_feedback}

### Previous Program
```python
{code}
```

### Previous Failed Test Case
{code_feedback}

### Reflection
'''
        logging.info('-'*50 + 'generate_reflection_with_history system' + '-'*50)
        logging.info(system_prompt)
        logging.info('-'*50 + 'generate_reflection_with_history user' + '-'*50)
        logging.info(user_prompt)

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        output = self.model.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        logging.info('-'*50 + 'generate_reflection_with_history assistant' + '-'*50)
        logging.info(output)

        return output

    def generate_reflexion_code_with_history(
            self,
            prompt: str,
            code: str,
            history: str,
            code_feedback: str,
            history_feedback: str,
            message: str,
            max_tokens: int = 1024,
            temperature: float = 0.2
    ) -> str:
        assert code_feedback != ''
        assert history_feedback != ''

        system_prompt = 'As a Python programmer, you are given a function signature and docstring, a program with its failed test case, and a previous fixed program and its failed test case, and an explanation why the program is still wrong. Your task is to write the corrected program. Use a Python code block to write your response.'
        user_prompt = f'''\
### Function Signature and Docstring
```python
{prompt}
```

### Program
```python
{history}
```

### Failed Test Case
{history_feedback}

### Previous Program
```python
{code}
```

### Previous Failed Test Case
{code_feedback}

### Reflection
{message}

### Improved Program
'''
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        logging.info('-'*50 + 'generate_reflexion_code_with_history system' + '-'*50)
        logging.info(system_prompt)
        logging.info('-'*50 + 'generate_reflexion_code_with_history user' + '-'*50)
        logging.info(user_prompt)

        output = self.model.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        logging.info('-'*50 + 'generate_reflexion_code_with_history assistant' + '-'*50)
        logging.info(output)

        code = extract_code(output)
        code = strip_code(code)
        return code
