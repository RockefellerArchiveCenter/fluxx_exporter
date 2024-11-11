import json
import logging
from pathlib import Path

import boto3
import paramiko
import requests

logging = logging.getLogger(__name__)


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

        logging.debug('Authenticating Fluxx client')
        # oauth parameters to retrieve token
        token_url = f"{base_url.rstrip('/')}/oauth/token"
        oauth_params = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        logging.debug("OAuth params created")

        self.session = requests.Session()
        logging.debug("Session initiated")

        # obtain oauth token
        try:
            logging.debug('Getting OAuth token.')
            response = self.session.post(token_url, data=oauth_params)
            response.raise_for_status()
            token = response.json()['access_token']
            logging.debug("OAuth token obtained")
        except Exception as e:
            logging.error(f"Could not obtain OAuth token with the supplied credentials: {e}")
            raise Exception(f"Could not obtain OAuth token with the supplied credentials: {e}")

        # Set Session request headers to persist connection
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
        logging.debug("Fluxx client authentication successful")

    def list_rows(self, entity_name, column_names, filter_value=None, related_entity=None, page=1, per_page=100):
        """Returns data about a given entity from Fluxx API.

        Args:
            entity_name (str): name of the entity to fetch
            column_names (list of str): column names from the entity
            filter_value (str): string to filter entities by
            related_entity (str): related entities to fetch
            page (int): page number to start from
            per_page (int): number of items per page

        Returns:
            rows (list): data about the requested entities.
        """
        logging.debug(f'Fetching data for {entity_name} with columns {column_names} and filter {filter_value}')

        params = {}
        # TODO pagination

        if page < 1:
            raise ValueError("Page integer must be greater than 0.")
        params.update({
            'cols': json.dumps(column_names),
            'page': page,
            'per_page': per_page
        })

        if filter_value:
            params.update({'filter': json.dumps(filter_value)})

        logging.debug(f'Params: {params}')

        try:
            resp = self.session.get(f"{self.api_url}{entity_name}", params=params)
            resp.raise_for_status()
            logging.debug(resp.json())
            return resp.json()['records'][entity_name]
        except Exception:
            logging.error(f"Error fetching data: {resp.text}")
            raise Exception(f"Error fetching data: {resp.text}")

    def download_document(self, document_id):
        """Downloads documents by ID.

        Args:
            document_id (str): ID for a document

        Returns:
            document_name, file (str, streaming file): document name and a streaming file object.
        """
        logging.debug(f'Fetching document {document_id}')
        document_id = str(document_id)
        download_params = {'cols': json.dumps(["document_file_name"])}

        # Get the filename
        document_info = self.session.get(
            f"{self.api_url}model_document/{document_id}",
            params=download_params)
        document_info.raise_for_status()
        document_name = document_info.json()['model_document']['document_file_name']

        # Get the file object
        document_download_url = f"{self.api_url}model_document_download/{document_id}"
        logging.debug(document_download_url)

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

        logging.debug('Instantiating S3 client')
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
        logging.debug(f'Starting upload of directory {directory}')
        for path in Path(directory).rglob("*"):
            if path.is_file():
                self.s3_client.upload_file(
                    str(path),
                    self.bucket,
                    str(path.relative_to(directory.parent)))
        logging.debug(f'Upload of directory {directory} complete')
