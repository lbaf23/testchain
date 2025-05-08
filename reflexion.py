"""
Reflexion

"""

from code_generator import CodeGenerator
from typing import Dict, List
from utils import read_jsonlines, save_jsonlines, create_dirs, load_config, append_jsonlines, config_log
from tqdm import tqdm
from code_evaluator import evaluator_factory, CodeEvaluator
from code_datasets import LocalDataset
from code_models import model_factory
import os
import argparse
import ast


def best_one(items: List[Dict]) -> Dict:
    assert len(items) > 0

    best = items[0]
    for p in items:
        if p['score'] > best['score']:
            best = p
    return best


def extract_function_calls(code):
    function_call = ''
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function_call = ast.unparse(node)
            break
    return function_call


def assert2call(stmt):
    return extract_function_calls(stmt)


def get_first_feedback(code, test_res) -> str:
    for t in test_res:
        if not t['passed']:
            if t['reason'] == 'assertion_error':
                try:
                    call = assert2call(t['test_case'])
                    code = code + '\n\n' + 'return_value = ' + call
                    exec_vars = {}
                    exec(code, exec_vars)
                    return_value = exec_vars['return_value']
                    if type(return_value) == str:
                        return_value = f'"{return_value}"'
                    else:
                        return_value = str(return_value)

                    msg = t['test_case'] + '  # program output: ' + return_value
                except Exception:
                    print(code)
                    raise ValueError
            else:
                msg = t['test_case'] + '  # program output: ' + t['reason']
            break
    return msg


def Reflexion(
        index: int,
        init_code: str,
        code_generator: CodeGenerator,
        data: Dict,
        tests: List[str],
        evaluator: CodeEvaluator,
        reflexion_config: Dict,
        result_file: str,
) -> None:
    rounds = reflexion_config['rounds']
    prompt = data['prompt']

    r = 0
    best = {'score': -1.0}
    
    # load result
    result = read_jsonlines(result_file)
    if len(result) > 0:
        r = result[-1]['r'] + 1
        best = result[-1]['best']
        code = result[-1]['item']['code']
        history = result[-1]['item']['history']
        code_feedback = result[-1]['item']['code_feedback']
        history_feedback = result[-1]['item']['history_feedback']

    td = tqdm(initial=r, total=rounds)
    td.set_description(f'''[{index}]''')

    if best['score'] == 1.0:
        return

    # repair
    while r < rounds:
        if r == 0:
            code = init_code
            history = ''
            reflection_message = ''
            code_feedback = ''
        elif r == 1:
            reflection_message = code_generator.generate_reflection(
                prompt=prompt,
                code=code,
                code_feedback=code_feedback,
            )
            new_code = code_generator.generate_reflexion_code(
                prompt=prompt,
                code=code,
                code_feedback=code_feedback,
                message=reflection_message
            )
            history = code
            code = new_code
        else:
            reflection_message = code_generator.generate_reflection_with_history(
                prompt=prompt,
                code=code,
                code_feedback=code_feedback,
                history=history,
                history_feedback=history_feedback,
            )
            new_code = code_generator.generate_reflexion_code_with_history(
                prompt=print,
                code=code_generator,
                code_feedback=code_feedback,
                history=history,
                history_feedback=history_feedback,
                message=reflection_message
            )
            history = code
            code = new_code

        code_res, test_res = evaluator.evaluate(code, tests)
        score = code_res['score']

        history_feedback = code_feedback
        if score < 1.0:
            code_feedback = get_first_feedback(code, test_res)
        else:
            code_feedback = ''

        item = {
            'r': r,
            'code': code,
            'code_feedback': code_feedback,
            'history': history,
            'history_feedback': history_feedback,
            'reflection_message': reflection_message,
            'score': score,
            'test_res': test_res
        }
        best = best_one([best, item])

        append_jsonlines(result_file, {
            'r': r,
            'item': item,
            'best': best
        })
        td.update(1)
        r += 1

        if best['score'] == 1.0:
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config/leetcode-hard/config-gpt4o-code.json')
    parser.add_argument('--run_type', type=str, default='reflexion')

    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=-1)

    parser.add_argument('--api_key', type=str, default='')
    parser.add_argument('--base_url', type=str, default='')

    parser.add_argument('--rerun', action='store_true')
    args = parser.parse_args()
    config = load_config(args.config)
    print(config, flush=True)

    dataset = LocalDataset(**config['dataset'])

    result_dir = os.path.join(config['result_dir'], args.run_type)
    log_dir = os.path.join(config['log_dir'], args.run_type)
    
    create_dirs(result_dir)
    create_dirs(log_dir)

    run_config = config[args.run_type]

    max_tests = 10
    tests_dir = os.path.join(config['result_dir'], run_config['tests'])
    init_code_dir = os.path.join(config['result_dir'], run_config['init_code'])

    extra_args = {}
    if args.api_key != '':
        extra_args['api_key'] = args.api_key
    if args.base_url != '':
        extra_args['base_url'] = args.base_url

    model = model_factory(**config['model'], **extra_args)
    code_generator = CodeGenerator(model)
    evaluator = evaluator_factory('py_asserts', 5.0)

    for i in dataset.data_range:
        if args.start < args.end and not args.start <= i < args.end:
            continue

        data = dataset.get_data(i)

        result_file = os.path.join(result_dir, f'result_{i}.jsonl')
        log_file = os.path.join(log_dir, f'log_{i}.log')
        config_log(log_file)

        codes_file = os.path.join(init_code_dir, f'result_{i}.jsonl')
        codes = read_jsonlines(codes_file)
        init_code = codes[0]['code']

        tests_file = os.path.join(tests_dir, f'result_{i}.jsonl')
        tests = read_jsonlines(tests_file)
        tests = [t['test_case'] for t in tests]
        tests = tests[ : max_tests]

        Reflexion(
            index=i,
            init_code=init_code,
            code_generator=code_generator,
            data=data,
            tests=tests,
            evaluator=evaluator,
            reflexion_config=run_config,
            result_file=result_file,
        )
