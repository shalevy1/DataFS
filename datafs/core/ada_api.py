from .datafs.managers import BaseDataManager

class DataApi(object):

    Services = {
    }

    Manager = BaseDataManager
    '''
    Data Manager

    When subclassing, replace with a specific manager, such as MongoDBManager
    '''

    DatabaseName = 'MyDatabase'
    DataTableName = 'DataFiles'

    def __init__(self):
        self._start_manager()
        self._start_services()

    def _start_manager(self, **config):
        self.manager = self.Manager(self, **config)

    def _start_services(self, **config):
        self.services = {}

        # make py3k compatible!!
        for servname, serv_class in self.Services.items():
            self.services[servname] = serv_class(self, **config)

    def create_archive(self, archive_name, **metadata):
        self.manager.create_archive(archive_name, **metadata)

    def get_archive(self, archive_name):
        self.manager.get_archive(archive_name)

    @property
    def archives(self):
        self.manager.get_archives()

    @archives.setter
    def archives(self):
        raise AttributeError('archives attribute cannot be set')
