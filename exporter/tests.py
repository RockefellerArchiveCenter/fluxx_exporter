import json
from pathlib import Path
from shutil import rmtree
from unittest.mock import call, patch

import botocore
import requests
import responses
from django.contrib.messages import ERROR, SUCCESS, get_messages
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from moto import mock_aws

from .clients import FluxxClient, S3Client
from .exporters import Exporter
from .forms import EntityColumnFormset, ExportJobWithEntities
from .models import Column, Entity, ExportJob, FluxxConfig, S3Config


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
        self.export_job = ExportJob.objects.create(
            name='Test Export',
            fluxx_config=self.fluxx_config,
            export_format='json',
            export_location='/tmp/exports/',
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

        """Missing export job throws a useful exception."""
        ExportJob.objects.all().delete()
        with self.assertRaises(Exception) as e:
            Exporter(100)
        self.assertIn("100", str(e.exception))

    @patch('exporter.exporters.Exporter.parse_filter')
    @patch('exporter.exporters.Exporter.parse_related_entities')
    @patch('exporter.exporters.Exporter.save_data')
    @patch('exporter.exporters.Exporter.save_document')
    @patch('exporter.clients.FluxxClient.__init__')
    @patch('exporter.clients.FluxxClient.list_rows')
    @patch('exporter.clients.FluxxClient.download_document')
    @patch('exporter.clients.S3Client.__init__')
    @patch('exporter.clients.S3Client.upload_directory')
    def test_fluxx_export(self, mock_s3_upload, mock_s3_init, mock_download_doc, mock_list_rows, mock_fluxx, mock_save_document, mock_save_data, mock_parse_related, mock_parse_filter):
        """Assert main method calls submethods with correct args"""

        # TODO test exception handling
        record_id = "12345"
        export_dir = Path(self.export_job.export_location, self.entity.name, record_id)
        model_doc_id = "12345"
        download_response = (1, 2)
        mock_fluxx.return_value = None
        mock_download_doc.return_value = download_response
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
        self.assertQuerySetEqual(mock_list_rows.call_args[0][1], [c.name for c in self.entity.column_set.all()])
        mock_list_rows.assert_called_once()

        mock_save_data.assert_called_once_with(
            mock_list_rows.return_value[0],
            self.export_job.export_format,
            export_dir)

        mock_save_document.assert_called_once_with(*download_response, export_dir)

        mock_download_doc.assert_called_once_with(model_doc_id)

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

    @patch('exporter.exporters.Exporter.write_csv')
    @patch('exporter.exporters.Exporter.write_json')
    @patch('exporter.exporters.Exporter.write_xml')
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
            call().raise_for_status(),
            call().json(),
            call(f'{self.base_url}/api/rest/v2/model_document_download/{document_id}', stream=True)]
        )
        self.assertIsInstance(doc, tuple)
        self.assertEqual(len(doc), 2)
        self.assertEqual(doc[0], file_name)


class S3ClientTests(TestCase):

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


class FormTests(TestCase):

    def setUp(self):
        self.fluxx_config = FluxxConfig.objects.create(
            name='Test Fluxx Config',
            base_url='https://fluxx.io',
            client_id="123456789",
            client_secret="abcdefg"
        )
        self.export_job = ExportJob.objects.create(
            name='Test Export',
            fluxx_config=self.fluxx_config,
            export_format='json',
            export_location='/tmp/exports/',
        )
        self.entity = Entity.objects.create(
            name='grant_request',
            export_job=self.export_job
        )
        self.column = Column.objects.create(
            name='organization_name',
            entity=self.entity
        )
        self.form_data = {
            'name': 'asdfa',
            'fluxx_config': self.fluxx_config.id,
            'export_location': 'asdf',
            'export_format': 'json',
            'entity_set-TOTAL_FORMS': '1',
            'entity_set-INITIAL_FORMS': '1',
            'entity_set-MIN_NUM_FORMS': '0',
            'entity_set-MAX_NUM_FORMS': '1000',
            'entity_set-0-id': self.entity.id,
            'entity_set-0-include_in_export': 'on',
            'column_set-TOTAL_FORMS': '1',
            'column_set-INITIAL_FORMS': '1',
            'column_set-MIN_NUM_FORMS': '0',
            'column_set-MAX_NUM_FORMS': '1000',
            'column_set-0-id': self.column.id,
            'column_set-0-include_in_export': 'on',
        }

    def test_custom_formset(self):
        """Assert creation of nested forms and custom validation."""

        form = ExportJobWithEntities(data=self.form_data)
        form.clean()
        for f in form.forms:
            self.assertIsInstance(f.nested, EntityColumnFormset)

        self.form_data.pop('column_set-0-include_in_export')
        form = ExportJobWithEntities(data=self.form_data)
        with self.assertRaises(ValidationError) as err:
            form.clean()
        self.assertEqual(err.exception.message, 'You must add at least one field to this column.')

        self.form_data.pop('entity_set-0-include_in_export')
        self.form_data['column_set-0-include_in_export'] = 'on'
        form = ExportJobWithEntities(data=self.form_data)
        with self.assertRaises(ValidationError) as err:
            form.clean()
        self.assertEqual(err.exception.message, 'You cannot export fields without also exporting the parent column.')


class ViewTests(TestCase):

    def setUp(self):
        self.fluxx_config = FluxxConfig.objects.create(
            name='Test Fluxx Config',
            base_url='https://fluxx.io',
            client_id="123456789",
            client_secret="abcdefg"
        )
        self.export_job = ExportJob.objects.create(
            name='Test Export',
            fluxx_config=self.fluxx_config,
            export_format='json',
            export_location='/tmp/exports/',
        )
        self.entity = Entity.objects.create(
            name='grant_request',
            export_job=self.export_job
        )
        self.column = Column.objects.create(
            name='organization_name',
            entity=self.entity
        )
        self.form_data = {
            'name': 'asdfa',
            'fluxx_config': self.fluxx_config.id,
            'export_location': 'asdf',
            'export_format': 'json',
            'entity_set-TOTAL_FORMS': '1',
            'entity_set-INITIAL_FORMS': '1',
            'entity_set-MIN_NUM_FORMS': '0',
            'entity_set-MAX_NUM_FORMS': '1000',
            'entity_set-0-id': self.entity.id,
            'entity_set-0-include_in_export': 'on',
            'column_set-TOTAL_FORMS': '1',
            'column_set-INITIAL_FORMS': '1',
            'column_set-MIN_NUM_FORMS': '0',
            'column_set-MAX_NUM_FORMS': '1000',
            'column_set-0-id': self.column.id,
            'column_set-0-include_in_export': 'on',
        }

    def test_create_export_job_view(self):
        """Assert custom behavior in get_context_data and is_valid."""
        response = self.client.get(reverse('exportjob_create'))
        self.assertIsInstance(response.context['formset'], ExportJobWithEntities)

        initial_entities = Entity.objects.all().count()
        initial_columns = Column.objects.all().count()
        response = self.client.post(reverse('exportjob_create'), self.form_data)
        self.assertEqual(Entity.objects.all().count(), initial_entities * 2)
        self.assertEqual(Column.objects.all().count(), initial_columns * 2)

    def test_update_export_job_view(self):
        """Assert custom behavior in get_context_data."""

        response = self.client.get(reverse('exportjob_update', kwargs={'pk': self.export_job.pk}))
        self.assertIsInstance(response.context['formset'], ExportJobWithEntities)

        initial_entities = Entity.objects.all().count()
        initial_columns = Column.objects.all().count()
        response = self.client.post(reverse('exportjob_update', kwargs={'pk': self.export_job.pk}), self.form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Entity.objects.all().count(), initial_entities)
        self.assertEqual(Column.objects.all().count(), initial_columns)

    @patch('exporter.exporters.Exporter.fluxx_export')
    @patch('exporter.exporters.Exporter.__init__')
    def test_run_export_job_view(self, mock_init, mock_export):
        """Assert view calls Exporter class and fluxx_export method with correct arguments."""

        mock_init.return_value = None
        mock_export.return_value = True, None
        resp = self.client.get(reverse('exportjob_run', kwargs={'pk': self.export_job.pk}))
        mock_init.assert_called_once_with(self.export_job.pk)
        mock_export.assert_called_once_with()
        self.assertEqual(resp.status_code, 200)
        success_messages = list(get_messages(resp.wsgi_request))
        self.assertEqual(len(success_messages), 1)
        self.assertEqual(success_messages[0].level, SUCCESS)
        self.assertEqual(str(success_messages[0]), 'Export completed successfully.')

        error = 'This is a detailed error message'
        mock_export.return_value = False, error
        resp = self.client.get(reverse('exportjob_run', kwargs={'pk': self.export_job.pk}))
        self.assertEqual(resp.status_code, 200)
        error_messages = list(get_messages(resp.wsgi_request))
        self.assertEqual(len(error_messages), 1)
        self.assertEqual(error_messages[0].level, ERROR)
        self.assertIn(error, str(error_messages[0]))


class ManagementCommandTests(SimpleTestCase):

    @patch('exporter.exporters.Exporter.fluxx_export')
    @patch('exporter.exporters.Exporter.__init__')
    def test_fluxx_export_command(self, mock_init, mock_export):
        """Assert ExportJob ID is passed to method and correct methods are called."""

        mock_init.return_value = None
        call_command("fluxx_export", 1)
        mock_init.assert_called_once_with(1)
        mock_export.assert_called_once_with()
