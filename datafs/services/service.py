
from __future__ import absolute_import

import os
import fs.utils
import fs.path
from fs.osfs import OSFS


class DataService(object):

    def __init__(self, fs):
        self.fs = fs

    def __repr__(self):
        return "<{}:{} object at {}>".format(self.__class__.__name__, self.fs.__class__.__name__, hex(id(self)))

    def upload(self, filepath, service_path):
        local = OSFS(os.path.dirname(filepath))
        
        if not self.fs.isdir(fs.path.dirname(service_path)):
            self.fs.makedir(
                fs.path.dirname(service_path),
                recursive=True,
                allow_recreate=True)

        fs.utils.copyfile(
            local,
            os.path.basename(filepath),
            self.fs,
            service_path)
