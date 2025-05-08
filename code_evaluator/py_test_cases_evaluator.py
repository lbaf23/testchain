from .code_evaluator import CodeEvaluator
from typing import List, Tuple, Dict
from .evaluator_utils import run_with_time_limit
from utils import StdUtils
import os


class PyTestCasesEvaluator(CodeEvaluator):
    def __init__(self, time_limit: float):
        """
        time_limit: time limit per test cases
        """
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        self.time_limit = time_limit

    def evaluate(self, code: str, test_cases: List[str]) -> Tuple[Dict, List[Dict]]:
        import sys
        sys.setrecursionlimit(10 ** 8)

        if type(test_cases) == dict:
            test_cases = [test_cases]

        test_cases_results = []
        passed = 0
        total = len(test_cases)

        std_utils = StdUtils()
        std_utils.redirect()

        for test_case in test_cases:
            codes = [code, test_case]
            res = run_with_time_limit(codes, self.time_limit)
            result = {
                'test_case': test_case,
                'passed': res[0],
                'reason': res[1]
            }
            test_cases_results.append(result)
            if result['passed']:
                passed += 1

        std_utils.recover()

        out = [{
            'score': 0 if total == 0 else float(passed) / total,
            'passed': passed,
            'total': total
        }, test_cases_results]

        return out
