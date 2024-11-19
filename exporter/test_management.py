from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from exporter.management.commands.import_html import \
    Command as ImportHtmlCommand

from .models import Field, Table


class FluxxExportCommandTests(TestCase):

    @patch('exporter.exporters.Exporter.fluxx_export')
    @patch('exporter.exporters.Exporter.__init__')
    def test_fluxx_export_command(self, mock_init, mock_export):
        """Assert ExportJob ID is passed to method and correct methods are called."""

        mock_init.return_value = None
        call_command("fluxx_export", 1)
        mock_init.assert_called_once_with(1)
        mock_export.assert_called_once_with()


class ImportCSVCommandTests(TestCase):

    def test_import_csv_command(self):
        """Assert import CSV command imports records as expected."""

        self.assertEqual(Field.objects.all().count(), 0)
        self.assertEqual(Table.objects.all().count(), 0)

        call_command('import_csv', 'exporter/fixtures/csv/fluxx_glossary_report.csv')

        self.assertEqual(Field.objects.all().count(), 380)
        self.assertEqual(Table.objects.all().count(), 6)

        with self.assertRaises(Exception) as err:
            call_command('import_csv', 'exporter/fixtures/csv/non_fluxx_glossary_report.csv')
        self.assertEqual(
            str(err.exception),
            'File exporter/fixtures/csv/non_fluxx_glossary_report.csv does not appear to be a Fluxx glossary csv.'
        )


class ImportHTMLCommandTests(TestCase):

    @patch('exporter.management.commands.import_html.Command.handle_row')
    @patch('exporter.management.commands.import_html.Command.get_table_data')
    def test_handle(self, mock_table_data, mock_handle_row):
        """Assert args and resulting objects"""

        mock_table_data.return_value = [
            {'name': 'updated_by_id', 'description': 'This is the ID of the user who update the record last.', 'permission': '[:create, :update]', 'data_type': 'User', 'related_class': 'User', 'type': 'relation', 'groupable?': 'Yes'},
            {'name': 'updated_at', 'description': "This is the date the record was last updated.  It is stored as UTC then formatted based on the current user's timezone.", 'permission': '[:create, :update]', 'data_type': 'datetime', 'related_class': '', 'type': 'column', 'groupable?': 'Yes'}
        ]

        call_command('import_html', 'exporter/fixtures/html/')

        mock_table_data.assert_called_once_with(Path('exporter/fixtures/html/grant_request.html'))
        self.assertEqual(mock_handle_row.call_count, 2)
        self.assertTrue(Table.objects.get(name='grant_request'))

    def test_parse_related_table_name(self):
        command = ImportHtmlCommand()

        fixtures = [
            ({'related_class': 'GrantRequest'}, 'grant_request'),
            ({'related_class': 'User'}, 'user')]

        for row, expected in fixtures:
            output = command.parse_related_table_name(row)
            self.assertEqual(output, expected)

    def test_row_is_field(self):
        command = ImportHtmlCommand()

        fixtures = [
            ({'type': ''}, False),
            ({'type': 'relation'}, False),
            ({'type': 'column'}, True)]

        for row, expected in fixtures:
            output = command.row_is_field(row)
            self.assertEqual(output, expected)

    def test_row_is_relation(self):
        command = ImportHtmlCommand()

        fixtures = [
            ({'related_class': 'User', 'type': 'relation'}, True),
            ({'related_class': '', 'type': 'relation'}, False),
            ({'related_class': '', 'type': 'column'}, False)]

        for row, expected in fixtures:
            output = command.row_is_relation(row)
            self.assertEqual(output, expected)

    def test_get_table_data(self):
        command = ImportHtmlCommand()

        for fp, expected in [
                ('exporter/fixtures/html/organization.html', 230),
                ('exporter/fixtures/html/user.html', 264),
                ('exporter/fixtures/html/grant_request.html', 352)]:
            output = command.get_table_data(fp)
            self.assertIsInstance(output, list)
            self.assertEqual(len(output), expected)
