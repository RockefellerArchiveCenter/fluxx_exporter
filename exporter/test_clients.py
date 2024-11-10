import json
from pathlib import Path
from unittest.mock import call, patch

import botocore
import requests
from django.test import SimpleTestCase
from moto import mock_aws

from .clients import FluxxClient, S3Client


class FluxxClientTests(SimpleTestCase):

    def setUp(self):
        self.access_token = "123456789abcdefg"
        self.base_url = "https://fluxx.io"
        self.client_id = "123456789"
        self.client_secret = "987654321"

    @patch('exporter.clients.FluxxClient.authenticate')
    def test_init(self, mock_authenticate):
        client = FluxxClient(self.base_url, self.client_id, self.client_secret)
        mock_authenticate.assert_called_once_with(self.base_url, self.client_id, self.client_secret)
        self.assertTrue(client.api_url.startswith(self.base_url))

    @patch('requests.Session.post')
    def test_authenticate(self, mock_post):
        """Asserts authentication is called correctly."""

        mock_post.return_value.json.return_value = {"access_token": self.access_token}
        client = FluxxClient(self.base_url, self.client_id, self.client_secret)
        mock_post.assert_called_once_with(
            f'{self.base_url}/oauth/token',
            data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret}
        )
        self.assertIsInstance(client.session, requests.Session)
        self.assertEqual(client.session.headers['Authorization'], f'Bearer {self.access_token}')

    @patch('requests.Session.post')
    @patch('requests.Session.get')
    def test_list_rows(self, mock_get, mock_post):
        """Asserts calls to Fluxx API and correct return value."""

        mock_post.return_value.json.return_value = {"access_token": self.access_token}
        client = FluxxClient(self.base_url, self.client_id, self.client_secret)

        entity_name = 'grant_request'
        column_names = ['id, model_documents', 'grant_id', 'grantee_owner_name']
        mock_get.return_value.json.return_value = {
            'records': {
                entity_name: [
                    {'id': 22617997, 'model_documents': [11218402, 11434734, 11434735], 'grant_id': 'R-2024-00003', 'grantee_owner_name': 'De Witt, Austin'},
                    {'id': 22618119, 'grant_id': 'R-2024-00006'},
                    {'id': 22674311, 'grant_id': 'G-2024-00008', 'grantee_owner_name': 'De Witt, Austin'}
                ]
            }, 'total_pages': 1, 'total_entries': 3, 'current_page': 1, 'per_page': 100}
        result = client.list_rows(entity_name, column_names)
        mock_get.assert_called_once_with(
            f'{self.base_url}/api/rest/v2/grant_request', params={'cols': json.dumps(column_names), 'page': 1, 'per_page': 100}
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    @patch('requests.Session.post')
    @patch('requests.Session.get')
    def test_download_document(self, mock_get, mock_post):
        """Asserts calls to Fluxx API and correct return from function."""

        mock_post.return_value.json.return_value = {"access_token": self.access_token}
        client = FluxxClient(self.base_url, self.client_id, self.client_secret)

        document_id = 11218402
        file_name = 'TestLineItems.csv'
        mock_get.return_value.json.return_value = {'model_document': {'id': document_id, 'document_file_name': file_name}}
        doc = client.download_document(document_id)
        mock_get.assert_has_calls([
            call(f'{self.base_url}/api/rest/v2/model_document/{document_id}', params={'cols': '["document_file_name"]'}),
            call().json(),
            call(f'{self.base_url}/api/rest/v2/model_document_download/{document_id}', stream=True)]
        )
        self.assertIsInstance(doc, tuple)
        self.assertEqual(len(doc), 2)
        self.assertEqual(doc[0], file_name)


class S3ClientTests(SimpleTestCase):

    def test_init(self):
        """Assert attributes are set as expected."""
        client = S3Client("bucket", "access_key_id", "secret_key", "us-east-1")
        self.assertEqual(client.bucket, "bucket")
        self.assertIsInstance(client.s3_client, botocore.client.BaseClient)

    @mock_aws
    def test_upload_directory(self):
        """Assert files are uploaded to S3 as expected."""
        bucket_name = "test_bucket"
        fixture_dir = Path('fixtures', 'grant_request_export')
        client = S3Client(bucket_name, "access_key_id", "secret_key", "us-east-1")
        client.s3_client.create_bucket(Bucket=bucket_name)
        client.upload_directory(fixture_dir)
        uploaded = [obj['Key'] for obj in client.s3_client.list_objects_v2(Bucket=bucket_name)['Contents']]
        local_dir = list(Path(fixture_dir).iterdir())
        for fp in local_dir:
            if fp.is_file():
                self.assertIn(str(fp.relative_to(fixture_dir.parent)), uploaded)
