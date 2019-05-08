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

import logging

from rbb_tools.commands import simserver
from rbb_tools.common import WorkingDirectory
from rbb_tools.tasks import InvalidTaskConfiguration


def simulate(config, api):
    if 'simulation' not in config:
        raise InvalidTaskConfiguration()

    logging.getLogger().addHandler(logging.StreamHandler())

    output = WorkingDirectory("", "/output", True)
    output.clean()

    manifest = simserver.simulate(api, config['simulation'], output_dir=output.get_directory_path())
    if not manifest:
        print("Failure in simserver.simulate, no manifest path returned")
        exit(1)

    if not simserver.upload(api, manifest, progress_indicator=False):
        print("Failure in simserver.upload")
        exit(1)

    print("Done!")
