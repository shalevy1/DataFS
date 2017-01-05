
from __future__ import absolute_import

from datafs.managers.manager import BaseDataManager
from datafs.core.data_archive import DataArchive

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError


class ConnectionError(IOError):
    pass


def catch_timeout(func):
    '''
    Decorator for wrapping MongoDB connections
    '''

    def inner(*args, **kwargs):
        msg = 'Connection to MongoDB server could not be established. '\
            'Make sure you are running a MongoDB server and that the MongoDB '\
            'Manager has been configured to connect over the correct port. '\
            'For more information see '\
            'https://docs.mongodb.com/manual/tutorial/.'
        try:
            return func(*args, **kwargs)
        except ServerSelectionTimeoutError:
            raise ConnectionError(msg)

    return inner


class MongoDBManager(BaseDataManager):
    '''
    Parameters
    ----------
    
    database_name : str
        Name of the database containing the DataFS tables

    table_name: str
        Name of the data archive table

    client_kwargs : dict
        Keyword arguments used in initializing a :py:class:`pymongo.MongoClient`
        object
    '''

    def __init__(self, database_name, table_name, client_kwargs={}):
        super(MongoDBManager, self).__init__(table_name)

        # setup MongoClient
        # Arguments can be passed to the client
        self._client_kwargs = client_kwargs
        self._client = MongoClient(**client_kwargs)

        self._database_name = database_name

        self._db = None
        self._coll = None
        self._spec_coll = None

    @property
    def config(self):
        config = {
            'database_name': self._database_name,
            'table_name': self._table_name,
            'client_kwargs': self._client_kwargs
        }

        return config

    @property
    def database_name(self):
        return self._database_name

    @property
    def table_name(self):
        return self._table_name

    @catch_timeout
    def _get_table_names(self):
        return self.db.collection_names(include_system_collections=False)

    def _create_archive_table(self, table_name):
        if table_name in self._get_table_names():
            raise KeyError('Table "{}" already exists'.format(table_name))

        self.db.create_collection(self.table_name)

        

        # something like create_archive for both docs


    def _create_spec_table(self, table_name):


        if self._spec_table_name in self._get_table_names():
            raise KeyError('Table "{}" already exists'.format(self._spec_table_name))

        self.db.create_collection(self._spec_table_name)

    def _delete_table(self, table_name):
        if table_name not in self._get_table_names():
            raise KeyError('Table "{}" not found'.format(table_name))

        self.db.drop_collection(table_name)

    @property
    def collection(self):
        table_name = self.table_name

        if table_name not in self._get_table_names():
            raise KeyError('Table "{}" not found'.format(table_name))


        return self.db[table_name]

    @property
    def spec_collection(self):

        spec_table_name = self._spec_table_name


        if spec_table_name not in self._get_table_names():
            raise KeyError('Table "{}" not found'.format(spec_table_name))

        return self.db[spec_table_name]
            

    @property
    def db(self):
        if self._db is None:
            self._db = self._client[self.database_name]

        return self._db



    # Private methods (to be implemented!)

    @catch_timeout
    def _update(self, archive_name, version_metadata):
        self.collection.update({"_id": archive_name},
                               {"$push": {"version_history": version_metadata}})

    def _update_metadata(self, archive_name, archive_metadata):
        for key, val in archive_metadata.items():
            self.collection.update({"_id": archive_name},
                                   {"$set": {"archive_metadata.{}".format(key): val}})

    def _update_spec_config(self,document_name, spec):

        # if self._spec_coll is None:
        #     self._spec_coll = self.db[self._]



        self.spec_collection.update_many({"_id": document_name}, {"$set": {'config': spec}}, upsert=True)

    @catch_timeout
    def _create_archive(
            self,
            archive_name,
            metadata):


        try:
            self.collection.insert_one(metadata)
        except DuplicateKeyError:
            raise KeyError('Archive "{}" already exists'.format(archive_name))

    def _create_if_not_exists(
            self,
            archive_name,
            metadata):

        try:
            self._create_archive(
                archive_name,
                metadata)

        except KeyError:
            pass


    @catch_timeout
    def _create_spec_config(self, table_name):

        if self._spec_coll == None:
            self._spec_coll = self.db[table_name + '.spec']

        itrbl = [{'_id': x, 'config': {}} 
                        for x in ('required_user_config', 'required_metadata_config')]



        try:
            self.spec_collection.insert_many(itrbl)
            #self.collection.insert_one()
        except TypeError as e:
            print(e)
            #raise KeyError('Spec config files already created for {}'.format(table_name))



    @catch_timeout
    def _get_archive_listing(self, archive_name):
        '''
        Return full document for ``{_id:'archive_name'}``

        .. note::

            MongoDB specific results - do not expose to user
        '''

        return self.collection.find_one({'_id': archive_name})

    def _get_archive_spec(self, archive_name):
        res = self._get_archive_listing(archive_name)

        if res is None:
            raise KeyError

        spec = ['authority_name', 'archive_path', 'versioned']
        
        return {k:v for k,v in res.items() if k in spec}

    def _get_authority_name(self, archive_name):

        res = self._get_archive_listing(archive_name)

        if res is None:
            raise KeyError

        return res['authority_name']

    def _get_archive_path(self, archive_name):

        res = self._get_archive_listing(archive_name)

        if res is None:
            raise KeyError

        return res['archive_path']

    def _get_archive_metadata(self, archive_name):

        res = self._get_archive_listing(archive_name)

        if res is None:
            raise KeyError

        return res['archive_metadata']

    def _get_version_history(self, archive_name):

        res = self.collection.find_one({'_id': archive_name})

        if res is None:
            raise KeyError

        return res['version_history']

    def _get_latest_hash(self, archive_name):

        version_history = self._get_version_history(archive_name)

        if len(version_history) == 0:
            return None

        else:
            return version_history[-1]['checksum']

    def _delete_archive_record(self, archive_name):

        return self.collection.remove({'_id': archive_name})

    def _get_archive_names(self):

        res = self.collection.find({}, {"_id": 1})

        return [r['_id'] for r in res]

    def _get_document_count(self):

        return self.spec_collection.count()

    def _get_spec_documents(self, table_name):
        return [item for item in self.spec_collection.find({})]


    def _get_required_user_config(self):

        return self.spec_collection.find_one({'_id': 'required_user_config'})['config']

    def _get_required_archive_metadata(self):
        
        return self.spec_collection.find_one({'_id': 'required_metadata_config'})['config']


    
