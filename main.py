from methods import TestChain, TestAgent, TestGenerator
from utils import config_log
from code_models import ModelBase, model_factory
from argparse import ArgumentParser
from code_datasets import LocalDataset
from code_evaluator import CodeEvaluator, evaluator_factory
import os
import logging
from utils import append_line, create_dirs, load_config, create_or_clear_file, init_cuda, is_syntax_valid


def generate_test_cases(
        model: ModelBase,
        evaluator: CodeEvaluator,
        prompt: str,
        entry_point: str,
        solution: str,
        result_file: str,
        mode: str,
        prompt_type: str
    ):
    if mode == 'TestGenerator':
        test_cases = TestGenerator(model).generate(
            function_def=prompt,
            prompt_type=prompt_type
        )
    elif mode == 'TestAgent':
        test_cases = TestAgent(model).generate(
            function_def=prompt,
            prompt_type=prompt_type
        )
    elif mode == 'TestChain':
        test_cases = TestChain(model).generate(
            function_def=prompt,
            prompt_type=prompt_type
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

    create_or_clear_file(result_file)
    for result in results:
        append_line(result_file, result)


def main():
    parser = ArgumentParser()
    parser.add_argument('--config', type=str, default='config/humaneval/config.json')
    parser.add_argument('--mode', type=str, choices=['TestGenerator', 'TestAgent', 'TestChain'])
    parser.add_argument('--prompt_type', type=str)

    parser.add_argument('--api_key', type=str, default='')
    parser.add_argument('--base_url', type=str, default='')

    parser.add_argument('--start', type=int, default=None)
    parser.add_argument('--end', type=int, default=None)
    args = parser.parse_args()
    config = load_config(args.config)
    print(config, flush=True)

    if config['model']['name'] == 'gpt35' or config['model']['name'] == 'gpt4':
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

    result_dir = os.path.join(config['result_dir'], f'{args.mode}_{args.prompt_type}')
    log_dir = os.path.join(config['log_dir'], f'{args.mode}_{args.prompt_type}')

    create_dirs(result_dir)
    create_dirs(log_dir)
    
    for i in dataset.data_range:
        data = dataset.get_data(i)
        result_file = os.path.join(result_dir, f'''result_{i}.jsonl''')
        log_file = os.path.join(log_dir, f'''log_{i}.log''')

        if os.path.exists(result_file):
            continue

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
            prompt_type=args.prompt_type
        )

    print('--- finished ---', flush=True)


if __name__ == '__main__':
    main()
