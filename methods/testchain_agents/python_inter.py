# from IPython.core.interactiveshell import InteractiveShell
from IPython.terminal.interactiveshell import TerminalInteractiveShell
from multiprocessing import Queue
import io
import sys
import signal
import shutil
import time


def handler(signum, frame):
    raise TimeoutError


class StdUtils:
    def __init__(self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def redirect(self):
        self.out_stream = io.StringIO()
        self.err_stream = io.StringIO()
        sys.stdout = self.out_stream
        sys.stderr = self.err_stream

    def recover(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def get_content(self):
        return self.out_stream.getvalue() + self.err_stream.getvalue()


class PyInterpreter:
    def __init__(self):
        self.ipython_dir = f'tmp-ipython-{time.time()}'
        self.create()

    def _run(self, code: str, q: Queue):
        std = StdUtils()
        std.redirect()
        self.shell.run_cell(code)
        std.recover()
        q.put(std.get_content())

    def run_cell(self, code: str, time_limit: float = 5):
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(time_limit)
        try:
            std = StdUtils()
            std.redirect()
            self.shell.run_cell(code)
            std.recover()
            output = std.get_content()
        except Exception:
            output = f'<TimeoutError: time limit = {time_limit} seconds>'
        finally:
            signal.alarm(0)

        if len(output) > 1024:
            output = output[: 1024] + ' ......'

        return output

    def run_cell_directly(self, code: str):
        std = StdUtils()
        std.redirect()
        self.shell.run_cell(code)
        std.recover()
        return std.get_content()

    presets = '''\
from typing import *
import math
'''

    def create(self):
        self.shell = TerminalInteractiveShell(ipython_dir=self.ipython_dir, colors='NoColor')
        self.shell.run_cell(self.presets)

    def clear(self):
        self.shell.run_cell(r'%reset -f')
        self.shell.run_cell(self.presets)

    def exit(self):
        self.shell.run_cell('exit()')
        self.shell.history_manager.end_session()
        shutil.rmtree(self.ipython_dir)
