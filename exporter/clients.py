import json
from pathlib import Path

import boto3
import paramiko
import requests

# TODO replace prints with logging


class FluxxClient(object):
    """Client for working with the Fluxx API"""

    def __init__(self, base_url, client_id, client_secret):
        # Optional style parameter, generally best kept as 'Full'
        # style = 'full'
        version = 'v2'
        base_url = base_url
        self.authenticate(
            base_url,
            client_id,
            client_secret)
        self.api_url = f"{base_url.rstrip('/')}/api/rest/{version}/"

    def authenticate(self, base_url, client_id, client_secret):
        """Authenticates the client against the Fluxx API"""
        # oauth parameters to retrieve token
        token_url = f"{base_url.rstrip('/')}/oauth/token"
        oauth_params = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }

        self.session = requests.Session()

        # obtain oauth token
        try:
            response = self.session.post(token_url, data=oauth_params)
        except Exception as e:
            raise Exception("Could not authenticate with the supplied credentials") from e

        # Set Session request headers to persist connection
        try:
            token = response.json()['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
        except BaseException:
            print("Could not find access token")

    def list_rows(self, entity_name, column_names, filter_value=None, related_entity=None, page=1, per_page=100):
        """Function to return a list of some number of rows and pages relating to an entity (or table)
        Filters can be applied following the format: <entity> <logic> <condition>
        Example: amount_requested eq 10000
        Filters can be tied together as follows: amount_requested eq 10000 and created_at today
        Filter logic will be requested and further documented at a later date
        """

        params = {}
        # TODO pagination

        if page < 1:
            raise ValueError("Page integer must be greater than 0.")
        print(f"columns: {json.dumps(column_names)}")
        params.update({
            'cols': json.dumps(column_names),
            'page': page,
            'per_page': per_page
        })

        if filter_value:
            params.update({'filter': json.dumps(filter_value)})

        try:
            resp = self.session.get(f"{self.api_url}{entity_name}", params=params)
            resp.raise_for_status()
            return resp.json()['records'][entity_name]
        except Exception as e:
            raise Exception(f"Error fetching data: {resp.text}") from e

    def download_document(self, document_id):
        document_id = str(document_id)
        download_params = {'cols': json.dumps(["document_file_name"])}

        # Get the filename
        document_info = self.session.get(
            f"{self.api_url}model_document/{document_id}",
            params=download_params)
        document_name = document_info.json()['model_document']['document_file_name']

        # Get the file object
        document_download_url = f"{self.api_url}model_document_download/{document_id}"

        return document_name, self.session.get(document_download_url, stream=True)


class SFTPClient(object):

    def __init__(self, host, port, username, password, remote_dir):

        self.remote_dir = remote_dir

        # Create an SSH client
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the server on port 22 (SFTP)
        self.ssh.connect(
            host,
            port=port,
            username=username,
            password=password)

        # Create an SFTP session from the SSH connection
        self.sftp = self.ssh.open_sftp()

    def upload_directory(self, local_dir):
        """Uploads files to a remote SFTP server.

        Args:
            local_dir (pathlib.Path)
        """
        # Normalize the local directory path
        local_dir = local_dir

        # Create remote directory if it does not exist
        try:
            self.sftp.mkdir(self.remote_dir)
        except IOError:
            pass  # Assume directory already exists

        for item in local_dir.iterdir():
            if item.is_file():
                remote_path = self.remote_dir / item.name
                self.sftp.put(str(item), str(remote_path))
            elif item.is_dir():
                remote_subdir = self.remote_dir / item.name
                try:
                    self.sftp.mkdir(str(remote_subdir))
                except IOError:
                    pass  # Directory might already exist
                self.upload_directory(self.sftp, item, remote_subdir)

    def close(self):
        """Closes SFTP connection"""
        self.sftp.close()
        self.ssh.close()


class S3Client(object):

    def __init__(self, bucket, access_key_id, secret_key, region):
        """Sets up client and other properties."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        self.bucket = bucket

    def upload_directory(self, directory):
        """Upload all files in the specified directory to an S3 bucket

        Args:
            directory: Directory containing files to upload

        Returns:
            None
        """
        for path in Path(directory).rglob("*"):
            if path.is_file():
                self.s3_client.upload_file(
                    str(path),
                    self.bucket,
                    str(path.relative_to(directory.parent)))
