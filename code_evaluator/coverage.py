from typing import List, Dict, Any, Tuple, Set
import sys


def remove_docstring(code: str):
    lines = code.split('\n')
    out = lines[0] + '\n'
    for i in range(1, len(lines)):
        if lines[i - 1].startswith('def') and lines[i].strip().startswith('"'):
            pass
        else:
            out += lines[i] + '\n'
    return out.strip()


def trace_exec_code(
        code_execs: List,
        time_limit: float,
        var=None,
        function_name=None
) -> Tuple[bool, Dict, Set]:
    if var is None:
        var = {}

    trace_lines = set()

    def trace_function(frame, event, arg=None):
        file_name = frame.f_code.co_filename
        co_name = frame.f_code.co_name
        line_no = frame.f_lineno

        if file_name != '<string>':
            return
        if function_name is None and event == 'line':
            trace_lines.add(int(line_no) - 1)
        elif function_name == co_name and event == 'line':
            trace_lines.add(int(line_no) - 1)
        return trace_function

    sys.settrace(trace_function)

    succeed = False
    # signal.signal(signal.SIGALRM, handler=handle_timeout)
    # signal.setitimer(signal.ITIMER_REAL, time_limit)
    try:
        for code_exec in code_execs:
            exec(code_exec, var)
        succeed = True
    except Exception:
        pass
    # finally:
    #     signal.alarm(0)
    #     sys.settrace(None)
    return succeed, var, trace_lines


def coverage(
        prefix: str,
        code: str,
        test_cases: List[str],
        time_limit: float = 5.0
) -> Tuple[float, List[int], List[int]]:
    prefix_lines = prefix.strip().split('\n')
    prefix_lines = [l for l in prefix_lines if l.strip() != '']

    code_lines = code.strip().split('\n')
    code_lines = [l for l in code_lines if l.strip() != '']

    code = '\n'.join(code_lines)

    lines = code_lines
    trace_lines = set()

    code_exec = compile(code, '<string>', 'exec')
    for test_case in test_cases:
        test_case_exec = compile(test_case, '<string>', 'exec')
        _, _, tr = trace_exec_code(
            code_execs=[code_exec, test_case_exec],
            time_limit=time_limit
        )
        trace_lines.update(tr)

    miss_lines = []

    passed = 0
    total = 0
    for i, l in enumerate(lines):
        l = l.strip()
        if l != 'else:' and l != '' and not (l.startswith('\'') and l.endswith('\'')) and i >= len(prefix_lines):
            if trace_lines.__contains__(i):
                passed += 1
                total += 1
            else:
                miss_lines.append(i)
                total += 1
    score = 0 if total == 0 else float(passed) / total

    return score, trace_lines, miss_lines
