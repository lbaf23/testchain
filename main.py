from methods import TestChain, TestAgent
from utils import config_log
from code_models import ModelBase, model_factory
from argparse import ArgumentParser
from code_datasets import LocalDataset
from code_evaluator import CodeEvaluator, evaluator_factory
import os
from tqdm import tqdm
import logging
from utils import append_line, create_dirs, read_file, load_config, create_or_clear_file, init_cuda, is_syntax_valid, \
    save_jsonlines, read_jsonlines


def generate_test_cases(
        model: ModelBase,
        evaluator: CodeEvaluator,
        prompt: str,
        entry_point: str,
        solution: str,
        result_file: str,
        mode: str,
        prompt_type: str,
        generate_temperature: float,
        calculate_temperature: float,
        tests_count: int = 10
):
    content = read_jsonlines(result_file)
    existing_test_cases = [c['test_case'] for c in content]

    if len(existing_test_cases) >= tests_count:
        return

    if mode == 'TestAgent':
        test_cases = TestAgent(model).generate(
            function_def=prompt,
            existing_test_cases=existing_test_cases,
            prompt_type=prompt_type,
            temperature=generate_temperature,
            tests_count=tests_count
        )
    elif mode == 'TestChain':
        content = read_jsonlines(f'{result_file}-test_input')
        existing_test_inputs = [c['test_input'] for c in content]

        test_cases, test_inputs = TestChain(model).generate(
            function_def=prompt,
            existing_test_inputs=existing_test_inputs,
            existing_test_cases=existing_test_cases,
            prompt_type=prompt_type,
            generate_temperature=generate_temperature,
            calculate_temperature=calculate_temperature,
            tests_count=tests_count
        )
    else:
        raise NotImplementedError

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

    # TestChain
    # save test inputs
    if mode == 'TestChain':
        content = []
        for i, input in enumerate(test_inputs):
            content.append({
                'index': i,
                'test_input': input
            })
        save_jsonlines(f'{result_file}-test_input', content)


def main():
    parser = ArgumentParser()
    parser.add_argument('--config', type=str, default='config/humaneval/config.json')
    parser.add_argument('--mode', type=str, choices=['TestAgent', 'TestChain'])
    parser.add_argument('--prompt_type', type=str)
    parser.add_argument('--generate_temperature', type=float, default=0.2,
                        help='temperature for TestAgent and TestChain (Designer Agent)')
    parser.add_argument('--calculate_temperature', type=float, default=0.2,
                        help='temperature for TestChain (Calculator Agent)')

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
        dataset_config['start'] = args.start
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

    result_dir = os.path.join(config['result_dir'], f'{args.mode}_{args.prompt_type}')
    log_dir = os.path.join(config['log_dir'], f'{args.mode}_{args.prompt_type}')

    create_dirs(result_dir)
    create_dirs(log_dir)

    for i in tqdm(dataset.data_range):
        data = dataset.get_data(i)
        result_file = os.path.join(result_dir, f'''result_{i}.jsonl''')
        log_file = os.path.join(log_dir, f'''log_{i}.log''')

        if args.rerun:
            create_or_clear_file(result_file)
            create_or_clear_file(log_file)

        config_log(log_file)

        logging.info(f'====== question {i} ======')

        generate_test_cases(
            model=model,
            evaluator=evaluator,
            prompt=data['prompt'],
            entry_point=data['entry_point'],
            solution=data['solution'],
            result_file=result_file,
            mode=args.mode,
            prompt_type=args.prompt_type,
            generate_temperature=args.generate_temperature,
            calculate_temperature=args.calculate_temperature,
            tests_count=args.tests_count
        )

    print('--- finished ---', flush=True)


if __name__ == '__main__':
    main()
