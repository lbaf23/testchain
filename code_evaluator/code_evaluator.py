from typing import Any, Tuple, Dict


class CodeEvaluator:
    def __init__(self, time_limit: float):
        self.time_limit = time_limit

    def evaluate(self, code: str, test_cases: Any) -> Tuple[Dict, Any]:
        """
        return: Tuple
            run_result: Dict
                score: float
                passed: int
                total: int
            test_cases_results: List[Dict]
                test_case: str
                passed: bool
                reason: float compile_error, runtime_error, timeout_error, assertion_error, other_error
        """
        raise NotImplementedError
