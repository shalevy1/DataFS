
from __future__ import absolute_import

import time
from datafs.config.helpers import check_requirements


class BaseDataManager(object):
    '''
    Base class for DataManager metadata store objects

    Should be subclassed. Not intended to be used directly.
    '''

    TimestampFormat = '%Y%m%d-%H%M%S'

    def __init__(self, table_name):

        self._table_name = table_name
        self._spec_table_name = table_name + '.spec'

        self._required_user_config = None
        self._required_archive_metadata = None

    @property
    def table_names(self):
        return self._get_table_names()

    @property
    def required_user_config(self):
        if self._required_user_config is None:
            user_config = self._get_required_user_config()
            assert isinstance(
                user_config, dict), 'sorry, user_config "{}" is a {}'.format(
                user_config, type(user_config))

            self._required_user_config = user_config

        return self._required_user_config

    @property
    def required_archive_metadata(self):
        if self._required_archive_metadata is None:
            archive_metadata = self._get_required_archive_metadata()
            assert isinstance(archive_metadata, dict)

            self._required_archive_metadata = archive_metadata

        return self._required_archive_metadata

    def create_archive_table(self, table_name, raise_on_err=True):
        '''

        Parameters
        -----------
        table_name: str

        Creates a table to store archives for your project
        Also creates and populates a table with basic spec for user and
        metadata config

        Returns
        -------
        None


        '''

        if raise_on_err:
            self._create_archive_table(table_name)
            self._create_spec_table(table_name)
            self._create_spec_config(table_name)

        else:
            try:
                self._create_archive_table(table_name)
                self._create_spec_table(table_name)
                self._create_spec_config(table_name)
            except KeyError:
                pass

    def update_spec_config(self, document_name, spec):
        '''
        Set the contents of a specification document by name

        This method should not be used directly. Instead, use
        :py:meth:`set_required_user_config` or
        :py:meth:`set_required_archive_metadata`.

        Parameters:
        document_name : str

            Name of a specification document's key

        spec : dict

            Dictionary metadata specification

        '''

        self._update_spec_config(document_name, spec)

    def set_required_user_config(self, user_config):
        '''
        Sets required user metadata for all users

        Parameters
        ----------
        user_config : dict

            Dictionary of required user metadata and metadata field
            descriptions. All archive creation and update actions will be
            required to have these keys in the user_config metadata.

            If the archive or version metadata does not contain these keys, an
            error will be raised with the descrtiption in the value associated
            with the key.

        '''

        self.update_spec_config('required_user_config', user_config)
        self._required_user_config = None

    def set_required_archive_metadata(self, metadata_config):
        '''
        Sets required archive metatdata for all users

        Parameters
        ----------
        metadata_config : dict

            Dictionary of required archive metada and metadata field
            descriptions. All archives created on this manager table will
            be required to have these keys in their archive's metadata.

            If the archive metadata does not contain these keys, an error
            will be raised with the description in the value associated with
            the key.

        '''

        self.update_spec_config('required_archive_metadata', metadata_config)
        self._required_archive_metadata = None

    def delete_table(self, table_name=None, raise_on_err=True):
        if table_name is None:
            table_name = self._table_name

        if raise_on_err:
            self._delete_table(table_name)
            self._delete_table(table_name + '.spec')
        else:
            try:
                self._delete_table(table_name)
            except KeyError:
                pass

    def update(self, archive_name, version_metadata):
        '''
        Register a new version for archive ``archive_name``

        .. note ::

            need to implement hash checking to prevent duplicate writes
        '''
        version_metadata['updated'] = self.create_timestamp()
        version_metadata['version'] = str(
            version_metadata.get('version', None))

        self._update(archive_name, version_metadata)

    def update_metadata(self, archive_name, archive_metadata):
        '''
        Update metadata for archive ``archive_name``
        '''

        self._update_metadata(archive_name, archive_metadata)

    def create_archive(
            self,
            archive_name,
            authority_name,
            archive_path,
            versioned,
            raise_on_err=True,
            metadata=None,
            user_config=None,
            helper=False):
        '''
        Create a new data archive

        Returns
        -------
        archive : object
            new :py:class:`~datafs.core.data_archive.DataArchive` object

        '''

        if metadata is None:
            metadata = {}

        if user_config is None:
            user_config = {}

        check_requirements(
            to_populate=user_config,
            prompts=self.required_user_config,
            helper=helper)

        check_requirements(
            to_populate=metadata,
            prompts=self.required_archive_metadata,
            helper=helper)

        archive_metadata = {
            '_id': archive_name,
            'authority_name': authority_name,
            'archive_path': archive_path,
            'versioned': versioned,
            'version_history': [],
            'archive_metadata': metadata
        }
        archive_metadata.update(user_config)

        archive_metadata['creation_date'] = archive_metadata.get(
            'creation_date', self.create_timestamp())

        if raise_on_err:
            self._create_archive(
                archive_name,
                archive_metadata)
        else:
            self._create_if_not_exists(
                archive_name,
                archive_metadata)

        return self.get_archive(archive_name)

    def get_archive(self, archive_name):
        '''
        Get a data archive given an archive name

        Returns
        -------
        archive_specification : dict
            archive_name: name of the archive to be retrieved
            authority: name of the archive's authority
            archive_path: service path of archive
        '''

        try:
            spec = self._get_archive_spec(archive_name)
            spec['archive_name'] = archive_name
            return spec

        except KeyError:
            raise KeyError('Archive "{}" not found'.format(archive_name))

    def get_metadata(self, archive_name):
        '''
        Retrieve the metadata for a given archive

        Parameters
        ----------
        archive_name : str
            name of the archive to be retrieved

        Returns
        -------
        metadata : dict
            current archive metadata
        '''

        return self._get_archive_metadata(archive_name)

    def get_latest_hash(self, archive_name):
        '''
        Retrieve the file hash for a given archive

        Parameters
        ----------
        archive_name : str
            name of the archive for which to retrieve the hash

        Returns
        -------
        hashval : str
            hash value for the latest version of archive_name

        '''

        return self._get_latest_hash(archive_name)

    def delete_archive_record(self, archive_name):
        '''
        Deletes an archive from the database

        Parameters
        ----------

        archive_name : str
            name of the archive to delete

        '''

        self._delete_archive_record(archive_name)

    def get_version_history(self, archive_name):
        return self._get_version_history(archive_name)

    @classmethod
    def create_timestamp(cls):
        '''
        Utility function for formatting timestamps

        Overload this function to change timestamp formats
        '''

        return time.strftime(cls.TimestampFormat, time.gmtime())


    def search(self, *search_terms):
        '''

        Parameters
        ----------
        search_terms: str
            strings  of terms to search for 


        >>> api.manager.search('annual', 'county', 'tas')
        >>> [ {u'_id': u'ACP_climate_smme_tas_county_daily_rcp85_pattern43_19810101-21001231.nc'},
        ... {u'_id': u'ACP_climate_smme_tas_county_mon_rcp85_pattern1_198101-210012.nc'},
        ... {u'_id': u'ACP_climate_smme_tas_county_daily_rcp45_access1-0_21000101-22001231.nc'},
        ... {u'_id': u'ACP_climate_smme_tas_county_mon_rcp26_mri-cgcm3_198101-210012.nc'}]
        '''

        return self._search(*search_terms)

    # Private methods (to be implemented by subclasses of DataManager)

    def _update(self, archive_name, version_metadata):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _create_archive(
            self,
            archive_name,
            archive_metadata):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _create_if_not_exists(
            self,
            archive_name,
            archive_metadata):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _get_archives(self):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _get_archive_metadata(self, archive_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _get_latest_hash(self, archive_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _get_authority_name(self, archive_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _get_archive_path(self, archive_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _delete_archive_record(self, archive_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _get_table_names(self):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _create_archive_table(self, table_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _create_spec_table(self, table_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _create_spec_config(self, table_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _update_spec_config(self, document_name, spec):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _delete_table(self, table_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _get_required_user_config(self):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _get_required_archive_metadata(self):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _get_version_history(self, archive_name):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')

    def _search(self, search_terms):
        raise NotImplementedError(
            'BaseDataManager cannot be used directly. Use a subclass.')



