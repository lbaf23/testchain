from .code_evaluator import CodeEvaluator
from .py_test_cases_evaluator import PyTestCasesEvaluator


def evaluator_factory(
        name: str,
        time_limit: float,
        **args
    ) -> CodeEvaluator:
    if name == 'py_asserts':
        return PyTestCasesEvaluator(time_limit)
    else:
        raise NotImplementedError
