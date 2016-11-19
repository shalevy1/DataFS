from __future__ import absolute_import

from datafs.services.service import DataService
from datafs.core.data_file import DataFile
from fs.osfs import OSFS


class OSDataFile(DataFile, OSFS):
    '''
    OSFS the native filesystem
    '''
    def __init__(self, api, archive, *args, **kwargs):
        DataFile.__init__(self, api, archive)
        OSFS.__init__(self, *args, **kwargs)



class OSService(DataService):
    '''
    Service providing an interface to the native filesystem
    '''
    
    FileConstructor = OSDataFile

    def __init__(self, api, archive, *args, **kwargs):
        DataService.__init__(self, api, archive, *args, **kwargs)

    def _get_datafile(self, archive_name, version_id):
        raise NotImplementedError

