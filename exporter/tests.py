from pathlib import Path
from shutil import rmtree
from unittest.mock import patch

import botocore
import requests
import responses
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from moto import mock_aws

from .clients import FluxxClient, S3Client
from .exporter import Exporter
from .models import (Column, Entity, ExportJob, FluxxConfig, S3Config,
                     SFTPConfig)


class ExportTests(TestCase):

    def setUp(self):
        # TODO move this to a fixture
        self.fluxx_config = FluxxConfig.objects.create(
            name='Test Fluxx Config',
            base_url='https://fluxx.io',
            client_id="123456789",
            client_secret="abcdefg"
        )
        self.s3_config = S3Config.objects.create(
            bucket='s3_bucket',
            access_key_id='123456789',
            secret_key='987654321',
            region='us-east-1'
        )
        self.sftp_config = SFTPConfig.objects.create(
            host='localhost',
            username='admin',
            password='password'
        )
        self.export_job = ExportJob.objects.create(
            name='Test Export',
            fluxx_config=self.fluxx_config,
            export_format='json',
            export_location='/tmp/exports/',
            sftp_config=self.sftp_config,
            s3_config=self.s3_config,
        )
        self.entity = Entity.objects.create(
            name='grant_request',
            export_job=self.export_job
        )
        self.column = Column.objects.create(
            name='organization_name',
            entity=self.entity
        )
        self.record = {
            "id": "1",
            "key": "value",
            "list": ["foo", "bar"],
            "dict": {"foo": "bar"},
            "nested": [{"foo": "bar"}]}

    def test_init(self):
        """Tests setting attributes and creation of base export location."""
        exporter = Exporter(self.export_job.pk)
        self.assertEqual(exporter.fluxx_config, self.export_job.fluxx_config)
        self.assertEqual(exporter.filter_string, self.export_job.filter_string)
        self.assertEqual(exporter.export_format, self.export_job.export_format)
        self.assertEqual(exporter.export_location, self.export_job.export_location)
        self.assertEqual(exporter.s3_config, self.export_job.s3_config)
        self.assertEqual(exporter.sftp_config, self.export_job.sftp_config)

        """Missing export job throws a useful exception."""
        ExportJob.objects.all().delete()
        with self.assertRaises(Exception) as e:
            Exporter(100)
        self.assertIn("100", str(e.exception))

    @patch('exporter.exporter.Exporter.parse_filter')
    @patch('exporter.exporter.Exporter.parse_related_entities')
    @patch('exporter.exporter.Exporter.save_data')
    @patch('exporter.exporter.Exporter.save_document')
    @patch('exporter.clients.FluxxClient.__init__')
    @patch('exporter.clients.FluxxClient.list_rows')
    @patch('exporter.clients.FluxxClient.download_document')
    @patch('exporter.clients.S3Client.__init__')
    @patch('exporter.clients.S3Client.upload_directory')
    @patch('exporter.clients.SFTPClient.__init__')
    @patch('exporter.clients.SFTPClient.upload_directory')
    @patch('exporter.clients.SFTPClient.close')
    def test_fluxx_export(self, mock_sftp_close, mock_sftp_upload, mock_sftp_init, mock_s3_upload, mock_s3_init, mock_download_doc, mock_list_rows, mock_fluxx, mock_save_document, mock_save_data, mock_parse_related, mock_parse_filter):
        """Assert main method calls submethods with correct args"""
        record_id = "12345"
        export_dir = Path(self.export_job.export_location, self.entity.name, record_id)
        model_doc_id = "12345"
        download_response = (1, 2)
        mock_fluxx.return_value = None
        mock_download_doc.return_value = download_response
        mock_sftp_init.return_value = None
        mock_s3_init.return_value = None
        mock_list_rows.return_value = [{"id": record_id, 'model_documents': [model_doc_id]}]

        Exporter(self.export_job.pk).fluxx_export()

        mock_fluxx.assert_called_once_with(
            self.fluxx_config.base_url,
            self.fluxx_config.client_id,
            self.fluxx_config.client_secret)
        mock_parse_filter.assert_called_once_with(self.export_job.filter_string)
        mock_parse_related.assert_called_once()

        self.assertEqual(mock_list_rows.call_args[0][0], self.entity.name)
        self.assertEqual(mock_list_rows.call_args[1]['filter_value'], mock_parse_filter.return_value)
        self.assertEqual(mock_list_rows.call_args[1]['related_entity'], mock_parse_related.return_value)
        self.assertQuerySetEqual(mock_list_rows.call_args[0][1], self.entity.column_set.all())
        mock_list_rows.assert_called_once()

        mock_save_data.assert_called_once_with(
            mock_list_rows.return_value[0],
            self.export_job.export_format,
            export_dir)

        mock_save_document.assert_called_once_with(*download_response, export_dir)

        mock_download_doc.assert_called_once_with(model_doc_id)

        mock_sftp_init.assert_called_once_with(
            self.sftp_config.host,
            self.sftp_config.port,
            self.sftp_config.username,
            self.sftp_config.password,
            self.sftp_config.remote_dir)
        mock_sftp_upload.assert_called_once_with(export_dir)
        mock_sftp_close.assert_called_once_with()

        mock_s3_init.assert_called_once_with(
            self.s3_config.bucket,
            self.s3_config.access_key_id,
            self.s3_config.secret_key,
            self.s3_config.region)
        mock_s3_upload.assert_called_once_with(export_dir)

    def test_parse_related_entity(self):
        """"Assert related entities are parsed as expected."""
        exporter = Exporter(self.export_job.pk)
        result = exporter.parse_related_entities([])
        self.assertEqual(result, {})

        entities = Entity.objects.all()
        result = exporter.parse_related_entities(entities)
        self.assertEqual(result, {self.entity.name: [self.column.name]})

    def test_parse_filter(self):
        """Assert filter is parsed as expected."""
        exporter = Exporter(self.export_job.pk)
        result = exporter.parse_filter("foo eq bar")
        self.assertEqual(result, ['foo', 'eq', 'bar'])

        """Exception raised when there are not three filter components."""
        with self.assertRaises(Exception) as e:
            exporter.parse_filter("foo eq")
        self.assertIn("foo eq", str(e.exception))

    @patch('exporter.exporter.Exporter.write_csv')
    @patch('exporter.exporter.Exporter.write_json')
    @patch('exporter.exporter.Exporter.write_xml')
    def test_save_data(self, mock_xml, mock_json, mock_csv):
        record = {}
        export_path = Path(self.export_job.export_location)
        exporter = Exporter(self.export_job.pk)

        exporter.save_data(record, 'csv', export_path)
        mock_csv.assert_called_once_with(record, export_path)
        mock_json.assert_not_called()
        mock_xml.assert_not_called()
        mock_csv.reset_mock()

        exporter.save_data(record, 'json', export_path)
        mock_json.assert_called_once_with(record, export_path)
        mock_csv.assert_not_called()
        mock_xml.assert_not_called()
        mock_json.reset_mock()

        exporter.save_data(record, 'xml', export_path)
        mock_xml.assert_called_once_with(record, export_path)
        mock_csv.assert_not_called()
        mock_json.assert_not_called()

    @responses.activate
    def test_save_document(self):
        exporter = Exporter(self.export_job.pk)
        doc_name = "test.txt"
        responses.add(
            responses.GET,
            'https://example.com/stream',
            body=b'\x00\x01\x02\x03',
            stream=True,
            content_type='application/octet-stream')
        response = requests.get('https://example.com/stream', stream=True)
        exporter.save_document(doc_name, response, Path(exporter.export_location))
        self.assertTrue(Path(exporter.export_location, doc_name).is_file())

    def test_write_csv(self):
        exporter = Exporter(self.export_job.pk)
        exporter.write_csv(self.record, exporter.export_location)
        self.assertTrue(Path(exporter.export_location, f'{self.record["id"]}.csv').is_file())
        # TODO assert content?

    def test_write_json(self):
        exporter = Exporter(self.export_job.pk)
        exporter.write_json(self.record, exporter.export_location)
        self.assertTrue(Path(exporter.export_location, f'{self.record["id"]}.json').is_file())
        # TODO assert content?

    def test_write_xml(self):
        exporter = Exporter(self.export_job.pk)
        exporter.write_xml(self.record, exporter.export_location)
        self.assertTrue(Path(exporter.export_location, f'{self.record["id"]}.xml').is_file())
        # TODO assert content?

    def tearDown(self):
        ExportJob.objects.all().delete()
        if Path(self.export_job.export_location).is_dir():
            rmtree(self.export_job.export_location)


class FluxxClientTests(TestCase):

    @patch('exporter.clients.FluxxClient.authenticate')
    def test_init(self, mock_authenticate):
        base_url = "https://fluxx.io"
        client_id = "123456789"
        client_secret = "987654321"
        client = FluxxClient(base_url, client_id, client_secret)
        mock_authenticate.assert_called_once_with(base_url, client_id, client_secret)
        self.assertTrue(client.api_url.startswith(base_url))

    def test_authenticate(self):
        pass

    def test_list_rows(self):
        # Test pagination
        pass

    def test_download_document(self):
        pass


class SFTPClientTests(TestCase):

    def test_init(self):
        pass

    def test_upload_directory(self):
        pass


class S3ClientTests(TestCase):

    def test_init(self):
        """Assert attributes are set as expected."""
        client = S3Client("bucket", "access_key_id", "secret_key", "us-east-1")
        self.assertEqual(client.bucket, "bucket")
        self.assertTrue(isinstance(client.s3_client, botocore.client.BaseClient))

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


class FormTests(TestCase):

    def test_custom_formset(self):
        # test custom behaviors in BaseEntitiesWithColumns
        pass


class ViewTests(TestCase):

    def test_create_export_job_view(self):
        # Test custom behaviors in get_context_data and form_valid
        pass

    def test_update_export_job_view(self):
        # Test custom behaviors in get_context_data and form_valid
        pass

    def test_run_export_job_view(self):
        # Test custom behavior in get
        pass


class ManagementCommandTests(SimpleTestCase):

    @patch('exporter.exporter.Exporter.fluxx_export')
    @patch('exporter.exporter.Exporter.__init__')
    def test_fluxx_export_command(self, mock_init, mock_export):
        """Assert ExportJob ID is passed to method and correc methods are called."""
        mock_init.return_value = None
        call_command("fluxx_export", 1)
        mock_init.assert_called_once_with(1)
        mock_export.assert_called_once_with()
