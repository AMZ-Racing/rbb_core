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
import shutil

from rbb_tools.common.shell import Command


def list(api):
    try:
        configs = api.list_extraction_configurations()

        for config in configs:
            print("- %s (%s)" % (config.name, config.type))
    except Exception as e:
        print("Error: " + str(e))


def download(api, config_name, target_directory, no_clean=False, tmp_dir=""):
    target_directory = os.path.realpath(target_directory)

    if not os.path.isdir(target_directory):
        print("Target directory is not a valid directory!")
        return False

    config = {}
    try:
        config = api.get_extraction_config(config_name)
    except Exception as e:
        print("Error: " + str(e))
        return False

    if tmp_dir == "":
        tmp_dir = "temp"

    tmp_dir = os.path.realpath(tmp_dir)
    if not os.path.isdir(tmp_dir):
        os.makedirs(tmp_dir)

    result = False
    if config.type == "git":
        result = download_git(api, config, target_directory, tmp_dir)
    else:
        print("Unknown config type '%s'!" % config.type)

    if not no_clean:
        shutil.rmtree(tmp_dir)

    return result


def download_git(api, config, target, tmp):
    clone_folder = tmp + "/git_config_" + config.name
    print("Downloading config with git into '%s'..." % clone_folder)

    if not 'git' in config.config:
        print("Git entry not defined in configuration!")
        return False

    if not 'url' in config.config['git']:
        print("URL not defined in configuration!")
        return False
    url = config.config['git']['url']

    if not 'branch' in config.config['git']:
        print("branch not defined in configuration!")
        return False
    branch = config.config['git']['branch']

    if not 'path' in config.config['git']:
        print("Path not defined in configuration!")
        return False
    path = config.config['git']['path']

    if (os.path.isdir(clone_folder)):
        print("Git repo exists already, so doing checkout&pull.")
        Command.execute("git checkout %s" % (branch), cwd=clone_folder)
        Command.execute("git pull", cwd=clone_folder)
    else:
        print("Git repo does not exist, so doing clone.")
        Command.execute("git clone -b %s --single-branch %s %s" % (branch, url, clone_folder))

    src_path = clone_folder + "/" + path
    files = os.listdir(src_path)
    for f in files:
        shutil.copy(src_path + "/" + f, target)

    return True