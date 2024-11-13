from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from .models import Column, Entity


class ManagementCommandTests(TestCase):

    @patch('exporter.exporters.Exporter.fluxx_export')
    @patch('exporter.exporters.Exporter.__init__')
    def test_fluxx_export_command(self, mock_init, mock_export):
        """Assert ExportJob ID is passed to method and correct methods are called."""

        mock_init.return_value = None
        call_command("fluxx_export", 1)
        mock_init.assert_called_once_with(1)
        mock_export.assert_called_once_with()

    def test_import_csv_command(self):
        """Assert import CSV command imports records as expected."""

        self.assertEqual(Column.objects.all().count(), 0)
        self.assertEqual(Entity.objects.all().count(), 0)

        call_command('import_csv', 'exporter/fixtures/fluxx_glossary_report.csv')

        self.assertEqual(Column.objects.all().count(), 380)
        self.assertEqual(Entity.objects.all().count(), 6)

        with self.assertRaises(Exception) as err:
            call_command('import_csv', 'exporter/fixtures/non_fluxx_glossary_report.csv')
        self.assertEqual(
            str(err.exception),
            'File exporter/fixtures/non_fluxx_glossary_report.csv does not appear to be a Fluxx glossary csv.'
        )
