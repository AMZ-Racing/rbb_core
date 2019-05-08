import os
import shutil


class WorkingDirectory(object):
    def __init__(self, path, fallback, is_temporary=False):

        if not path:
            path = os.getcwd() + fallback

        path = os.path.abspath(path)

        # Add a subdirectory to the path so that it can be removed easily later
        # Otherwise if the users would specify the home dir as temp, we would
        # remove the home dir
        if is_temporary:
            if os.path.exists(path):
                path = path + "/will-be-removed"

        if not os.path.exists(path):
            os.makedirs(path)

        self._path = path
        self._is_temporary = is_temporary

    def get_directory_path(self):
        return self._path

    def get_path(self, file_path):
        return self.get_directory_path() + "/" + file_path;

    def clean(self):
        if self._is_temporary:
            # Clear by deleting and recreating
            shutil.rmtree(self._path)
            os.makedirs(self._path)