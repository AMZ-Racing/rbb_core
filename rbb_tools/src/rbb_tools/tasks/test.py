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
import sys

from rbb_client import Configuration
from rbb_tools.tasks import InvalidTaskConfiguration

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess


def success(config, api):
    return "success"


def ping(config, api):
    print(Configuration().to_debug_report())
    return "Ping succeeded"


def causes_exception(config, api):
    i = 10 / 0
    return "Will never return"


def exits(config, api):
    exit(10)


def waits(config, api):
    import time
    print("Waiting 10 seconds")
    time.sleep(10)


def invalid_config(config, api):
    raise InvalidTaskConfiguration()


def long_task_streaming(config, api):
    import time

    for i in range(10 * 6):
        echo_cmd = ["echo", "Echoed by an external process.\n"]
        subprocess.Popen(echo_cmd)
        print("Print by an internal statement. %f \n" % (time.time()))
        sys.stderr.write("This goes to stderr \n")
        time.sleep(10)
