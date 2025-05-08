"""
Pytester-770M

https://github.com/awsm-research/pytester

"""

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from typing import List
from utils import is_syntax_valid, save_jsonlines, create_dirs
from tqdm import tqdm


class PyTesterModel():
    def __init__(self):
        model_name = '../models/pytester-770M'
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, device_map='auto')
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            truncation_side='left',
            padding_side='right',
            do_lower_case=False
        )

    def generate(self, prompt: str, entry_point: str, nums: int = 10) -> List[str]:
        prompt = f'''\
{prompt.strip()}
    pass
# check the correctness of {entry_point}
assert'''
        
        print('--- input ---')
        print(prompt)

        inputs = self.tokenizer(prompt, padding=True, truncation=True, max_length=512, return_tensors='pt').to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            min_new_tokens=5,
            max_new_tokens=300,
            pad_token_id=self.tokenizer.eos_token_id,
            num_return_sequences=nums,
            num_beams=nums
        )
        outputs = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        for i in range(nums):
            if outputs[i].__contains__('\n'):
                outputs[i] = outputs[i][ : outputs[i].index('\n')]
        outputs = ['assert ' + o.strip() for o in outputs]
        return outputs


import argparse
from code_datasets import LocalDataset
from code_evaluator import evaluator_factory
if __name__ == '__main__':
    model = PyTesterModel()
    e = evaluator_factory(name='py_asserts', time_limit=1.0)

    parser = argparse.ArgumentParser()
    parser.add_argument('--ds', type=str, default='humaneval', choices=['humaneval', 'leetcode-hard'])
    parser.add_argument('--prompt_type', type=str, default='', choices=['wo', 'full'])
    args = parser.parse_args()

    ds = args.ds
    prompt_type = args.prompt_type

    if ds == 'humaneval':
        dataset = LocalDataset('humaneval', 'data/humaneval-wo-examples.jsonl')
    elif ds == 'leetcode-hard':
        dataset = LocalDataset('leetcode-hard', 'data/leetcode-hard-wo-examples.jsonl')
    else:
        raise NotImplementedError(f'Unknown dataset: {ds}')

    save_dir = f'result/{ds}/pytester-770M/Tests_{prompt_type}'
    create_dirs(save_dir)

    for i in tqdm(dataset.data_range):
        data = dataset.get_data(i)

        prompt = data['prompt'] if prompt_type == 'wo' else data['prompt_full']
        code = data['solution']
        entry_point = data['entry_point']

        tests = model.generate(prompt, entry_point)
        results = []
        tests_set = set()
        for t in tests:
            if tests_set.__contains__(t):
                results.append({
                    'index': len(results),
                    'test_case': t,
                    'correct': False,
                    'reason': 'duplicated'
                })
            elif not t.__contains__(entry_point):
                results.append({
                    'index': len(results),
                    'test_case': t,
                    'correct': False,
                    'reason': 'no_entry_point'
                })
            elif not is_syntax_valid(t):
                results.append({
                    'index': len(results),
                    'test_case': t,
                    'correct': False,
                    'reason': 'syntax_invalid'
                })
            else:
                res, res1 = e.evaluate(code, [t])
                if res['score'] == 1.0:
                    results.append({
                        'index': len(results),
                        'test_case': t,
                        'correct': True,
                        'reason': ''
                    })
                else:
                    results.append({
                        'index': len(results),
                        'test_case': t,
                        'correct': False,
                        'reason': res1[0]['reason']
                    })
    
            tests_set.add(t)
        

        result_file = f'{save_dir}/result_{i}.jsonl'
        save_jsonlines(result_file, results)
