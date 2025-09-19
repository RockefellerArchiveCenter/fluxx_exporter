from unittest.mock import patch

from django.test import TestCase

from .models import DocumentType, FluxxConfig


class FluxxConfigTests(TestCase):

    @patch('exporter.clients.FluxxClient.authenticate')
    @patch('exporter.clients.FluxxClient.list_rows')
    def test_save(self, mock_list, mock_authenticate):
        """Asserts custom save behavior"""
        mock_list.return_value = [{"name": "foo", "id": 1}, {"name": "baz", "id": 2}]
        FluxxConfig(
            name="test_config",
            base_url="https://fluxx.io/api/",
            client_id="12345",
            client_secret="54321").save()

        mock_authenticate.assert_called_once_with('https://fluxx.io/api/', '12345', '54321')
        mock_list.assert_called_once_with('model_document_type', field_names=['name', 'id'])
        self.assertEqual(len(DocumentType.objects.all()), 2)
