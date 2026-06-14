import json
import logging
from pathlib import Path

import boto3
import paramiko
from requests_ratelimiter import LimiterSession

logging = logging.getLogger(__name__)


class FluxxClient(object):
    """Client for working with the Fluxx API"""

    def __init__(self, base_url, client_id, client_secret):
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

        self.session = LimiterSession(per_minute=180)
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

    def request(self, method, url, params=None, data=None):
        """Handle HTTP request."""
        logging.debug(f'Making {method} request for {url} with params {params} and data {data}')
        try:
            resp = getattr(self.session, method)(url, params=params, data=data)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logging.error(f"Error making {method.upper()} request from {url}: {resp.text}")
            raise Exception(f"Error making {method.upper()} request from {url}: {resp.text}")

    def get(self, url, params=None):
        """Handle a request for a single page."""
        return self.request('get', url, params=params)

    def list(self, url, data=None):
        """Handle a paged request."""
        table_name = url.rstrip('/').split('/')[-2]
        current_page = data['page']
        resp = self.request('post', url, data=data)
        total_pages = resp['total_pages']
        for record in resp['records'][table_name]:
            yield record
        while total_pages > current_page:
            current_page += 1
            data.update({'page': current_page})
            resp = self.request('post', f"{self.api_url}{table_name}/list", data=data)
            for record in resp['records'][table_name]:
                yield record

    def list_rows(self, table_name, field_names, filter_value=None, grant_ids=None, relations=None, current_page=1, per_page=100):
        """Returns data about a given table from Fluxx API.

        Args:
            table_name (str): name of the table to fetch
            field_names (list of str): field names from the table
            filter_value (list): list representing a filter
            grant_ids (list): IDs for grants to retrieve
            relations (str): relation params
            current_page (int): page number to start from
            per_page (int): number of items per page

        Returns:
            rows (list): data about the requested tables.
        """
        logging.debug(f'Fetching data for {table_name} with fields {field_names}, filter {filter_value} and grant_ids {grant_ids}')

        params = {'cols': json.dumps(field_names)}

        if relations:
            params.update({'relation': json.dumps(relations)})

        if grant_ids:
            grant_filter = {
                "group_type": "or",
                "conditions": [["id", "eq", g_id] for g_id in grant_ids]
            }

            filter_value = (
                grant_filter
                if not filter_value
                else {
                    "group_type": "and",
                    "conditions": [filter_value, grant_filter],
                }
            )

        if filter_value:
            params.update({'filter': json.dumps(filter_value)})

        params.update({
            'page': current_page,
            'per_page': per_page
        })
        logging.debug(f'Params: {params}')
        yield from self.list(f"{self.api_url}{table_name}/list", data=params)

    def get_document_info(self, document_id):
        """Gets information for a document by ID.

        Args:
            document_id (str): ID for a document

        Returns:
            document_info (dict): Information about the specified document
        """
        logging.debug(f'Fetching document information for {document_id}')
        document_id = str(document_id)
        params = {'cols': json.dumps(["document_file_name", "model_document_master_id", "seq_number"])}

        return self.get(f"{self.api_url}model_document/{document_id}", params=params)['model_document']

    def download_document(self, document_id,):
        """Downloads a document by ID.

        Args:
            document_id (str): ID for a document

        Returns:
            file (streaming file): streaming file object.
        """
        document_download_url = f"{self.api_url}model_document_download/{document_id}"
        logging.debug(document_download_url)

        return self.session.get(document_download_url, stream=True)


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


class AmazonS3Client(object):

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
