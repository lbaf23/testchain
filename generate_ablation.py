from methods import TestChain
from utils import config_log, extract_first_block, save_jsonlines, read_file, write_file
from code_models import ModelBase, model_factory
from argparse import ArgumentParser
from code_datasets import LocalDataset
from code_evaluator import CodeEvaluator, evaluator_factory
import os
from typing import *
import logging
from tqdm import tqdm
from utils import append_line, read_jsonlines, create_dirs, load_config, create_or_clear_file, init_cuda, is_syntax_valid


def generate_code(model, prompt: str) -> str:
    # generate code
    system_prompt = 'You are a Python programmer.'
    user_prompt = f'''\
Write the implementation for this function, write your result in a Python code block.
```python
{prompt}
```
'''
    output = model.generate_chat(
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        stop_strs=[],
        max_tokens=1024,
        temperature=0.2
    )

    logging.info('-' * 20 + 'calculator agent generate code [system]' + '-' * 20)
    logging.info(system_prompt)
    logging.info('-' * 20 + 'calculator agent generate code [user]' + '-' * 20)
    logging.info(user_prompt)
    logging.info('-' * 20 + 'calculator agent generate code [assistant]' + '-' * 20)
    logging.info(output)

    code = extract_first_block(output)
    return code



def generate_test_chain_directly(
        model: ModelBase,
        evaluator: CodeEvaluator,
        prompt: str,
        entry_point: str,
        solution: str,
        mode: str,
        test_inputs_result_file: str,
        result_file: str,
        tests_count: int = 10
):
    # load result
    content = read_jsonlines(result_file)
    existing_test_cases = [c['test_case'] for c in content]
    if len(existing_test_cases) >= tests_count:
        return

    # load test inputs
    content = read_jsonlines(test_inputs_result_file)
    test_inputs = []
    for c in content:
        test_inputs.append(c['test_input'])
    test_inputs = test_inputs[ : tests_count]
    test_inputs = test_inputs[len(existing_test_cases) : ]

    # load code
    code = ''
    if mode == 'code':
        if os.path.exists(f'{result_file}-code'):
            code = read_file(f'{result_file}-code')
        else:
            code = generate_code(model, prompt)
            write_file(f'{result_file}-code', code)

        additional_test_cases = TestChain(model).generate_wo_reasoning(
            test_inputs=test_inputs,
            function_def=prompt,
            entry_point=entry_point,
            code=code,
            mode=mode,
        )
    elif mode == 'reasoning':
        additional_test_cases = TestChain(model).generate_wo_code(
            test_inputs=test_inputs,
            function_def=prompt,
            entry_point=entry_point
        )
    elif mode == 'directly':
        additional_test_cases = TestChain(model).generate_wo_code_and_reasoning(
            test_inputs=test_inputs,
            function_def=prompt,
            entry_point=entry_point
        )
    else:
        raise NotImplementedError

    test_cases = existing_test_cases + additional_test_cases

    results = []
    test_cases_set = set()
    for i, test_case in enumerate(test_cases):
        result = {
            'index': i,
            'test_case': test_case
        }

        if test_cases_set.__contains__(test_case):
            result['correct'] = False
            result['reason'] = 'duplicated'
        elif not test_case.__contains__(entry_point):
            result['correct'] = False
            result['reason'] = 'no_entry_point'
        elif not is_syntax_valid(test_case):
            result['correct'] = False
            result['reason'] = 'syntax_invalid'
        else:
            res, res1 = evaluator.evaluate(
                solution,
                [test_case]
            )
            if res['score'] == 1.0:
                result['correct'] = True
                result['reason'] = ''
            else:
                result['correct'] = False
                result['reason'] = res1[0]['reason']

        test_cases_set.add(test_case)
        results.append(result)

    save_jsonlines(result_file, results)


def main():
    parser = ArgumentParser()
    parser.add_argument('--config', type=str, default='config/leetcode-hard/config-gpt4o.json')
    parser.add_argument('--mode', type=str, default='code', choices=['code', 'reasoning', 'directly'])
    
    parser.add_argument('--tests_count', type=int, default=10)
    parser.add_argument('--api_key', type=str, default='')
    parser.add_argument('--base_url', type=str, default='')

    parser.add_argument('--start', type=int, default=None)
    parser.add_argument('--end', type=int, default=None)

    parser.add_argument('--rerun', action='store_true')
    args = parser.parse_args()
    config = load_config(args.config)
    print(config, flush=True)

    if config['model']['name'] == 'api':
        pass
    else:
        init_cuda()

    dataset_config = config['dataset']
    if args.start != None:
        dataset_config['start'] =  args.start
    if args.end != None:
        dataset_config['end'] = args.end

    extra_args = {}
    if args.api_key != '':
        extra_args['api_key'] = args.api_key
    if args.base_url != '':
        extra_args['base_url'] = args.base_url

    evaluator = evaluator_factory(**config['evaluator'])
    dataset = LocalDataset(**dataset_config)
    model = model_factory(**config['model'], **extra_args)

    testchain_result_dir = os.path.join(config['result_dir'], f'TestChain_py_inter')
    result_dir = f'{testchain_result_dir}_{args.mode}'
    log_dir = os.path.join(config['log_dir'], f'TestChain_py_inter_{args.mode}')

    create_dirs(result_dir)
    create_dirs(log_dir)
    
    for i in tqdm(dataset.data_range):
        data = dataset.get_data(i)
        result_file = os.path.join(result_dir, f'result_{i}.jsonl')
        test_inputs_result_file = os.path.join(testchain_result_dir, f'result_{i}.jsonl-test_input')
        log_file = os.path.join(log_dir, f'''log_{i}.log''')

        if args.rerun:
            create_or_clear_file(result_file)
            create_or_clear_file(log_file)

        config_log(log_file)

        logging.info(f'====== question {i} ======')

        generate_test_chain_directly(
            model=model,
            evaluator=evaluator,
            prompt=data['prompt'],
            entry_point=data['entry_point'],
            solution=data['solution'],
            mode=args.mode,
            test_inputs_result_file=test_inputs_result_file,
            result_file=result_file,
            tests_count=args.tests_count
        )

    print('--- finished ---', flush=True)


if __name__ == '__main__':
    main()
