from typing import List, Tuple
from multiprocessing import Process, Queue


def runner(codes: List, q: Queue):
    execs = []
    for code in codes:
        try:
            execs.append(compile(code, '<string>', 'exec'))
        except Exception:
            q.put([False, 'compile_error'])
            return

    vars = {}
    for e in execs:
        try:
            exec(e, vars)
        except AssertionError:
            q.put([False, 'assertion_error'])
            return
        except Exception:
            q.put([False, 'runtime_error'])
            return

    q.put([True, ''])


def run_with_time_limit(codes: List, time_limit: float) -> Tuple[bool, str]:
    timeout_error = [False, 'timeout_error']
    q = Queue()
    p = Process(target=runner, args=(codes, q,))
    p.start()
    p.join(time_limit)
    if p.is_alive():
        p.terminate()
        p.join()
        return timeout_error
    try:
        return q.get(block=False)
    except Exception:
        return timeout_error
