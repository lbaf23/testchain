from typing import List
from code_evaluator import CodeEvaluator


def bugs_pass_rate(test_cases: List, code_with_bugs: List, evaluator: CodeEvaluator):
    if len(test_cases) == 0:
        return 0

    total = len(code_with_bugs)
    passed = 0
    for bugs in code_with_bugs:
        code = bugs['code']
        result, _ = evaluator.evaluate(code, test_cases)
        if result['score'] < 1.0:  # find the bug
            passed += 1
    return float(passed) / total
