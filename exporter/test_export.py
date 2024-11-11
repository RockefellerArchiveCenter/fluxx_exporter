from pathlib import Path
from shutil import rmtree
from unittest.mock import patch

import requests
import responses
from django.test import TestCase

from .exporters import Exporter
from .models import Column, Entity, ExportJob, FluxxConfig, S3Config


class ExportTests(TestCase):

    fixtures = ['initial.json']

    def setUp(self):
        self.record = {
            "id": "1",
            "key": "value",
            "list": ["foo", "bar"],
            "dict": {"foo": "bar"},
            "nested": [{"foo": "bar"}]}

    def test_init(self):
        """Tests setting attributes and creation of base export location."""

        export_job = ExportJob.objects.all().first()
        exporter = Exporter(export_job.pk)
        self.assertEqual(exporter.fluxx_config, export_job.fluxx_config)
        self.assertEqual(exporter.filter_string, export_job.filter_string)
        self.assertEqual(exporter.export_format, export_job.export_format)
        self.assertEqual(exporter.export_location, export_job.export_location)
        self.assertEqual(exporter.s3_config, export_job.s3_config)

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

        record_id = "12345"
        export_job = ExportJob.objects.all().first()
        fluxx_config = FluxxConfig.objects.all().first()
        s3_config = s3_config = S3Config.objects.all().first()
        entity = Entity.objects.all().first()
        export_dir = Path(export_job.export_location, entity.name, record_id)
        model_doc_id = "12345"
        download_response = (1, 2)
        mock_fluxx.return_value = None
        mock_download_doc.return_value = download_response
        mock_s3_init.return_value = None
        mock_list_rows.return_value = [{"id": record_id, 'model_documents': [model_doc_id]}]

        output = Exporter(export_job.pk).fluxx_export()

        self.assertEqual(output, (True, None))

        mock_fluxx.assert_called_once_with(
            fluxx_config.base_url,
            fluxx_config.client_id,
            fluxx_config.client_secret)
        mock_parse_filter.assert_called_once_with(export_job.filter_string)
        mock_parse_related.assert_called_once()

        self.assertEqual(mock_list_rows.call_args[0][0], entity.name)
        self.assertEqual(mock_list_rows.call_args[1]['filter_value'], mock_parse_filter.return_value)
        self.assertEqual(mock_list_rows.call_args[1]['related_entity'], mock_parse_related.return_value)
        self.assertQuerySetEqual(mock_list_rows.call_args[0][1], [c.name for c in entity.column_set.all()])
        mock_list_rows.assert_called_once()

        mock_save_data.assert_called_once_with(
            mock_list_rows.return_value[0],
            export_job.export_format,
            export_dir)

        mock_save_document.assert_called_once_with(*download_response, export_dir)

        mock_download_doc.assert_called_once_with(model_doc_id)

        mock_s3_init.assert_called_once_with(
            s3_config.bucket,
            s3_config.access_key_id,
            s3_config.secret_key,
            s3_config.region)
        mock_s3_upload.assert_called_once_with(export_dir)

        # Test exception handling
        error_message = "This is an error!"
        mock_fluxx.side_effect = Exception(error_message)
        output = Exporter(export_job.pk).fluxx_export()
        self.assertEqual(output[0], False)
        self.assertIn(error_message, output[1])

    def test_parse_related_entity(self):
        """"Assert related entities are parsed as expected."""
        export_job = ExportJob.objects.all().first()
        entity = Entity.objects.all().first()
        column = Column.objects.all().first()
        exporter = Exporter(export_job.pk)
        result = exporter.parse_related_entities([])
        self.assertEqual(result, {})

        entities = Entity.objects.all()
        result = exporter.parse_related_entities(entities)
        self.assertEqual(result, {entity.name: [column.name]})

    def test_parse_filter(self):
        """Assert filter is parsed as expected."""
        export_job = ExportJob.objects.all().first()
        exporter = Exporter(export_job.pk)
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
        export_job = ExportJob.objects.all().first()
        record = {}
        export_path = Path(export_job.export_location)
        exporter = Exporter(export_job.pk)

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
        export_job = ExportJob.objects.all().first()
        exporter = Exporter(export_job.pk)
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
        export_job = ExportJob.objects.all().first()
        exporter = Exporter(export_job.pk)
        exporter.write_csv(self.record, exporter.export_location)
        self.assertTrue(Path(exporter.export_location, f'{self.record["id"]}.csv').is_file())
        # TODO assert content?

    def test_write_json(self):
        export_job = ExportJob.objects.all().first()
        exporter = Exporter(export_job.pk)
        exporter.write_json(self.record, exporter.export_location)
        self.assertTrue(Path(exporter.export_location, f'{self.record["id"]}.json').is_file())
        # TODO assert content?

    def test_write_xml(self):
        export_job = ExportJob.objects.all().first()
        exporter = Exporter(export_job.pk)
        exporter.write_xml(self.record, exporter.export_location)
        self.assertTrue(Path(exporter.export_location, f'{self.record["id"]}.xml').is_file())
        # TODO assert content?

    def tearDown(self):
        rmtree('/tmp/exports/', ignore_errors=True)
