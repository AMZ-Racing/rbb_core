# AMZ-Driverless
#  Copyright (c) 2019 Authors:
#   - Huub Hendrikx <hhendrik@ethz.ch>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import shlex
import sys
import time
import signal
from contextlib import contextmanager

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess

try:
    from subprocess import DEVNULL  # Python 3.
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


class Colors:
    # Taken from Blender
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def colorize(text, color, no_color=False):
        if no_color:
            return text
        else:
            return color + text + Colors.ENDC


def fileno(file_or_fd):
    fd = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd


@contextmanager
def stream_redirected(to_stream=os.devnull, from_stream=None):
    # Based upon https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python
    if from_stream is None:
       from_stream = sys.stdout

    from_stream_fd = fileno(from_stream)
    with os.fdopen(os.dup(from_stream_fd), 'wb') as copied:
        from_stream.flush()
        try:
            os.dup2(fileno(to_stream), from_stream_fd)
        except ValueError:
            with open(to_stream, 'wb') as to_file:
                os.dup2(to_file.fileno(), from_stream_fd)
        try:
            yield from_stream
        finally:
            from_stream.flush()
            os.dup2(copied.fileno(), from_stream_fd)


class CommandGroup:

    def __init__(self):
        self.commands = []

    def Command(self, *args, **kwargs):
        cmd = Command(*args, **kwargs)
        self.commands.append(cmd)
        return cmd

    def ensure_terminated(self):
        for cmd in self.commands:
            cmd.ensure_terminated(cmd._cmd[0])


class Command:

    @staticmethod
    def execute(cmd, env=None, cwd=None):
        command = Command(cmd, env=env, cwd=cwd)
        command.run(capture=True)
        returncode = command.join()
        stdout, stderr = command.get_captured_output()
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        if returncode != 0:
            raise RuntimeError("non zero exit code %d" % returncode)

    def __init__(self, cmd, env=None, cwd=None):
        self._cmd = shlex.split(cmd)
        self._env = os.environ.copy()
        self._cwd = cwd
        self._popen = None
        self._captured = False
        self._captured_stdout = None
        self._captured_stderr = None

        if env is None:
            env = {}

        for key, value in env.iteritems():
            self._env[key] = value

    def run(self, capture=False):
        if capture:
            self._captured = True
            self._popen = subprocess.Popen(self._cmd,
                                           env=self._env,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, cwd=self._cwd)
        else:
            self._popen = subprocess.Popen(self._cmd, env=self._env, stdout=DEVNULL, cwd=self._cwd)

    def is_running(self):
        if self._popen:
            self._popen.poll()
            if self._popen.returncode is None:
                return True
        return False

    def send_sigint(self):
        if self._popen:
            self._popen.send_signal(signal.SIGINT)

    def join(self):
        while self.is_running():
            time.sleep(1)

        if self._captured:
            self._captured_stdout = self._popen.stdout.read()
            self._captured_stderr = self._popen.stderr.read()
            return self._popen.returncode
        else:
            return self._popen.returncode

    def get_captured_output(self):
        return self._captured_stdout, self._captured_stderr

    def ensure_terminated(self, status=""):
        if self._popen:
            self._popen.poll()

            if self._popen.returncode is None:
                self._popen.terminate()
                time.sleep(0.2)
                self._popen.poll()

            while self._popen.returncode is None:
                time.sleep(1)
                if status:
                    print(status)
                self._popen.poll()