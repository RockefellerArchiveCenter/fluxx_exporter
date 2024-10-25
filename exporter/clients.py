import json
import os
from pathlib import Path

import boto3
import paramiko
import requests

from exporter.models import Column, Entity

# TODO replace prints with logging
# TODO clarify purpose of unused variables
# TODO replace os with path


class FluxxClient(object):
    """Client for working with the Fluxx API"""

    def __init__(self, config):
        # version = config.version
        # Optional style parameter, generally best kept as 'Full'
        # style = 'full'
        base_url = config.base_url
        self.session = self.authenticate(
            base_url,
            config.application_id,
            config.secret)
        self.api_url = f"{base_url.rstrip('/')}/api/rest/v2/"

    def authenticate(self, base_url, application_id, secret):
        """Authenticates the client against the Fluxx API"""
        # oauth parameters to retrieve token
        token_url = f"{base_url.rstrip('/')}/oauth/token"
        oauth_params = {
            'grant_type': 'client_credentials',
            'client_id': application_id,
            'client_secret': secret
        }

        self.session = requests.Session()

        # obtain oauth token
        try:
            response = self.session.post(token_url, data=oauth_params)
        except Exception as e:
            raise Exception("Could not authenticate with the supplied credentials") from e

        # Set Session request headers to persist connection
        try:
            self.token = response.json()['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
        except BaseException:
            print("Could not find access token")

    def list_rows(self, entity, columns, page=1, per_page=100,
                  filter=None, related_entity=None):
        """Function to return a list of some number of rows and pages relating to an entity (or table)
        Filters can be applied following the format: <entity> <logic> <condition>
        Example: amount_requested eq 10000
        Filters can be tied together as follows: amount_requested eq 10000 and created_at today
        Filter logic will be requested and further documented at a later date
        """

        if page < 1:
            raise ValueError("Page integer must be greater than 0.")
        print(f"columns: {json.dumps(columns)}")
        list_params = {
            'cols': json.dumps(columns),
            'page': page,
            'per_page': per_page
        }

        if filter:
            list_params.update({
                'filter': json.dumps(filter)
            })

        if related_entity:
            entity_id = Entity.objects.get(name=entity).id

            related_entity_objects = Entity.objects.filter(
                related_entity=entity_id)

            for related_entity in related_entity_objects:
                related_entity_id = Entity.objects.get(name=related_entity).id
                print(f"related_entity: {related_entity.name}")
                re_columns = [
                    column.name for column in Column.objects.filter(
                        entity=related_entity_id)]
                print(f"re_columns: {re_columns}")

                # Directly assign the list to relation_params
                relation_params = {related_entity.name: re_columns}

                list_params.update({
                    # Directly assign the list to relation_params
                    'relation': json.dumps(relation_params),
                })

        print(list_params)

        return self.session.get(self.api_url + entity, params=list_params)

    def download_document(self, document_id, sub_folder_path):
        document_id = str(document_id)
        download_params = {'cols': json.dumps(["document_file_name"])}

        # Get the filename and type
        document_info = self.session.get(
            f"{self.api_url}model_document/{document_id}",
            params=download_params)
        document_name = document_info.json()['model_document']['document_file_name']

        # Get the file and save to respective folder
        document_download_url = f"{self.api_url}model_document_download/{document_id}"
        response = self.session.get(document_download_url, stream=True)

        # Ensure the Documents directory exists
        documents_path = Path(sub_folder_path, 'Documents')
        documents_path.mkdir(exist_ok=True)

        with open(Path(documents_path / document_name), 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)


class SFTPClient(object):

    def __init__(self, config):

        self.remote_dir = config.remotedir

        # Create an SSH client
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the server on port 22 (SFTP)
        self.ssh.connect(
            config.hostname,
            port=config.port,
            username=config.username,
            password=config.password)

        # Create an SFTP session from the SSH connection
        self.sftp = self.ssh.open_sftp()

    def put_directory(self, local_dir):
        # Normalize the local directory path
        local_dir = os.path.normpath(local_dir)

        # Create remote directory if it does not exist
        try:
            self.sftp.mkdir(self.remote_dir)
        except IOError:
            pass  # Assume directory already exists

        # Recursively upload files and directories
        for root, dirs, files in os.walk(local_dir):

            # Calculate the relative path from the local directory
            rel_path = os.path.relpath(root, local_dir)
            remote_path = os.path.join(self.remote_dir, rel_path).replace('\\', '/')

            for dir_name in dirs:
                remote_subdir = os.path.join(
                    remote_path, dir_name).replace(
                    '\\', '/')
                try:
                    self.sftp.mkdir(remote_subdir)
                except IOError:
                    pass

            for file_name in files:
                local_file = os.path.join(root, file_name)
                remote_file = os.path.join(
                    remote_path, file_name).replace(
                    '\\', '/')
                self.sftp.put(local_file, remote_file)
                print(f"Uploaded {local_file} to {remote_file}")

    def close(self):
        self.sftp.close()
        self.ssh.close()


class S3Client(object):

    def __init__(self, config):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            aws_region=config.region
        )
        self.bucket = config.bucket

    def upload_directory(self, directory):
        """Upload all files in the specified directory to an S3 bucket

        :param directory: Directory containing files to upload
        :param bucket: Bucket to upload to
        :param access_key: AWS Access Key ID
        :param secret_key: AWS Secret Access Key
        :return: None
        """
        # List all files in the directory
        for root, dirs, files in os.walk(directory):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                # Create the object key with the date folder and subdirectory
                # structure
                relative_path = os.path.relpath(file_path, directory)
                object_name = f"{relative_path}".replace("\\", "/")
                try:
                    # Upload the file
                    self.s3_client.upload_file(file_path, self.bucket, object_name)
                    print(f"{file_name} has been uploaded to {self.bucket}/{object_name}")
                except Exception as e:
                    print(f"Failed to upload {file_name} to {self.bucket}: {e}")
