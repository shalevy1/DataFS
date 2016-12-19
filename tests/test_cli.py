from datafs.managers.manager_mongo import MongoDBManager
from datafs.managers.manager_dynamo import DynamoDBManager
import tempfile
import os
from datafs.datafs import DataFSInterface



def test_cli_local():
    
    # setup manager table

    table_name = 'my-cli-test-table'

    manager = DynamoDBManager(table_name, 
    						session_args={ 
            								'aws_access_key_id': "access-key-id-of-your-choice",
    										'aws_secret_access_key': "secret-key-of-your-choice",}, 
            				resource_args={ 
            								'endpoint_url':'http://localhost:8000/','region_name':'us-east-1'}
        					)

    manager.create_archive_table(table_name, raise_if_exists=False)

    # setup data directory

    temp = tempfile.mkdtemp()

    my_test_yaml = '''
    default-profile: myapi
    profiles:
      myapi:
        api:
          user_config:
            username: 'My Name'
            contact: 'my.email@example.com'

        authorities:
          local:
            args:
              - {}
            service: OSFS

        cache: {{}}

        manager:
          class: DynamoDBManager
          
          kwargs:
            resource_args: {endpoint_url:'http://localhost:8000/', region_name: 'us-east-1'}
            session_args: { 
      			aws_access_key_id: "access-key-id-of-your-choice",
    			aws_secret_access_key: "secret-key-of-your-choice",},
            table_name: 'my-cli-test-table'
    '''.format(temp)


    fp = tempfile.NamedTemporaryFile(delete=False)
    with open(fp, 'w+') as f:
        f.write(my_test_yaml)

    result = runner.invoke(cli, ['--config-file', '"{}"'.format(fp), '--profile', 'default-profile', 'create-archive', 'my_first_archive', '--description', 'My test data archive'])
    assert result.output == '<DataArchive local://my_first_archive>'

    result = runner.invoke(cli, ['--config-file', '"{}"'.format(fp), '--profile', 'default-profile', 'metadata', 'my_first_archive'])
    assert result.output == "{'metadata': 'my_first_archive'}"

    # teardown

    shutil.rmtree(temp)
    manager.delete_table(table_name)
    os.remove(fp)