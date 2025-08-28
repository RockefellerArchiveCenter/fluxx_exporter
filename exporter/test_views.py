from unittest.mock import ANY, patch

from django.contrib.messages import ERROR, SUCCESS, get_messages
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from .forms import ExportJobWithFilters, ExportJobWithTables
from .models import ExportJob, Field, Table
from .views import ImportTablesView


class ExportJobViewTests(TestCase):

    fixtures = ['initial.json']

    def setUp(self):
        self.form_data = {
            'name': 'Export Job',
            'fluxx_config': '1',
            'export_location': '/tmp/exports',
            'export_format': 'json',
            'grant_ids': '1,2,3,4',
            'amazon_s3_config': '1',
            'filters-TOTAL_FORMS': '0',
            'filters-INITIAL_FORMS': '1',
            'table_set-TOTAL_FORMS': '2',
            'table_set-INITIAL_FORMS': '2',
            'table_set-MIN_NUM_FORMS': '0',
            'table_set-MAX_NUM_FORMS': '1000',
            'table_set-0-id': '2',
            'table_set-0-include_in_export': 'on',
            'tablefield-table_set-0-fields-TOTAL_FORMS': '1',
            'tablefield-table_set-0-fields-INITIAL_FORMS': '1',
            'tablefield-table_set-0-fields-MIN_NUM_FORMS': '0',
            'tablefield-table_set-0-fields-MAX_NUM_FORMS': '1000',
            'tablefield-table_set-0-fields-0-id': '2',
            'tablefield-table_set-0-fields-0-include_in_export': 'on',
            'table_set-1-id': '3',
            'table_set-1-include_in_export': 'on',
            'tablefield-table_set-1-fields-TOTAL_FORMS': '1',
            'tablefield-table_set-1-fields-INITIAL_FORMS': '1',
            'tablefield-table_set-1-fields-MIN_NUM_FORMS': '0',
            'tablefield-table_set-1-fields-MAX_NUM_FORMS': '1000',
            'tablefield-table_set-1-fields-0-id': '3',
            'tablefield-table_set-1-fields-0-include_in_export': 'on'
        }

    def test_create_export_job_view(self):
        """Assert custom behavior in get_context_data and is_valid."""
        response = self.client.get(reverse('exportjob_create'))
        self.assertIsInstance(response.context['formset'], ExportJobWithTables)
        self.assertIsInstance(response.context['filters'], ExportJobWithFilters)
        self.assertIn('grant_request_forms', response.context)
        self.assertIn('connected_table_forms', response.context)

        response = self.client.post(reverse('exportjob_create'), self.form_data)
        self.assertEqual(Table.objects.all().count(), 5)
        self.assertEqual(Field.objects.all().count(), 6)

    def test_update_export_job_view(self):
        """Assert custom behavior in get_context_data."""

        export_job = ExportJob.objects.all().first()
        response = self.client.get(reverse('exportjob_update', kwargs={'pk': export_job.pk}))
        self.assertIsInstance(response.context['formset'], ExportJobWithTables)
        self.assertIsInstance(response.context['filters'], ExportJobWithFilters)
        self.assertIn('grant_request_forms', response.context)
        self.assertIn('connected_table_forms', response.context)

        initial_tables = Table.objects.all().count()
        initial_fields = Field.objects.all().count()
        response = self.client.post(reverse('exportjob_update', kwargs={'pk': export_job.pk}), self.form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Table.objects.all().count(), initial_tables)
        self.assertEqual(Field.objects.all().count(), initial_fields)

    @patch('exporter.exporters.Exporter.fluxx_export')
    @patch('exporter.exporters.Exporter.__init__')
    def test_run_export_job_view(self, mock_init, mock_export):
        """Assert view calls Exporter class and fluxx_export method with correct arguments."""

        mock_init.return_value = None
        mock_export.return_value = True, None
        export_job = ExportJob.objects.all().first()
        resp = self.client.get(reverse('exportjob_run', kwargs={'pk': export_job.pk}))
        mock_init.assert_called_once_with(export_job.pk)
        mock_export.assert_called_once_with()
        self.assertEqual(resp.status_code, 200)
        success_messages = list(get_messages(resp.wsgi_request))
        self.assertEqual(len(success_messages), 1)
        self.assertEqual(success_messages[0].level, SUCCESS)
        self.assertEqual(str(success_messages[0]), 'Export completed successfully.')

        error = 'This is a detailed error message'
        mock_export.return_value = False, error
        resp = self.client.get(reverse('exportjob_run', kwargs={'pk': export_job.pk}))
        self.assertEqual(resp.status_code, 200)
        error_messages = list(get_messages(resp.wsgi_request))
        self.assertEqual(len(error_messages), 1)
        self.assertEqual(error_messages[0].level, ERROR)
        self.assertIn(error, str(error_messages[0]))


class ImportViewTests(TestCase):

    def setUp(self):
        class FormData(object):
            pass

        self.view = ImportTablesView(request=HttpRequest())
        self.form_data = FormData()

    @patch('exporter.views.ImportTablesView.handle_row')
    @patch('exporter.views.ImportTablesView.get_table_data')
    @patch('exporter.views.ImportTablesView.get_related_tables_dict')
    @patch('django.contrib.messages.add_message')
    def test_form_valid(self, mock_message, mock_related_tables_dict, mock_table_data, mock_handle_row):
        """Assert args and resulting objects"""

        mock_table_data.return_value = "grant_request", [
            {'name': 'updated_by_id', 'description': 'This is the ID of the user who update the record last.', 'permission': '[:create, :update]', 'data_type': 'User', 'related_class': 'User', 'type': 'relation', 'groupable?': 'Yes'},
            {'name': 'updated_at', 'description': "This is the date the record was last updated.  It is stored as UTC then formatted based on the current user's timezone.", 'permission': '[:create, :update]', 'data_type': 'datetime', 'related_class': '', 'type': 'column', 'groupable?': 'Yes'}
        ]
        mock_related_tables_dict.return_value = {}

        self.form_data.cleaned_data = {
            'grant_request_file': 'grant_request',
            'related_tables_files': ['related_table']
        }

        self.view.form_valid(self.form_data)

        mock_table_data.assert_called_once_with('grant_request')
        self.assertEqual(mock_handle_row.call_count, 2)
        self.assertTrue(Table.objects.get(name='grant_request'))
        mock_related_tables_dict.assert_called_once_with(['related_table'])
        mock_message.assert_called_once_with(ANY, SUCCESS, '2 tables imported successfully.')

    def test_parse_related_table_name(self):
        fixtures = [
            ({'related_class': 'GrantRequest'}, 'grant_request'),
            ({'related_class': 'User'}, 'user')]

        for row, expected in fixtures:
            output = self.view.parse_related_table_name(row)
            self.assertEqual(output, expected)

    def test_row_is_field(self):
        fixtures = [
            ({'type': ''}, False),
            ({'type': 'relation'}, False),
            ({'type': 'column'}, True)]

        for row, expected in fixtures:
            output = self.view.row_is_field(row)
            self.assertEqual(output, expected)

    def test_row_is_relation(self):
        fixtures = [
            ({'related_class': 'User', 'type': 'relation'}, True),
            ({'related_class': '', 'type': 'relation'}, False),
            ({'related_class': '', 'type': 'column'}, False)]

        for row, expected in fixtures:
            output = self.view.row_is_relation(row)
            self.assertEqual(output, expected)

    def test_get_table_data(self):
        for filepath, expected_title, expected_data_len in [
                ('exporter/fixtures/html/organization.html', 'organization', 230),
                ('exporter/fixtures/html/user.html', 'user', 264),
                ('exporter/fixtures/html/grant_request.html', 'grant_request', 352)]:
            with open(filepath, 'r') as fp:
                table_name, data = self.view.get_table_data(fp)
                self.assertIsInstance(data, list)
                self.assertEqual(table_name, expected_title)
                self.assertEqual(len(data), expected_data_len)

    @patch('exporter.views.ImportTablesView.get_table_data')
    def test_get_related_tables_dict(self, mock_table_data):
        mock_table_data.side_effect = [('related_file', []), ('another_related_file', [])]

        output = self.view.get_related_tables_dict(['related_file', 'another_related_file'])

        self.assertEqual(mock_table_data.call_count, 2)
        self.assertEqual(output, {'related_file': [], 'another_related_file': []})

    def test_get_normalized_title(self):
        for raw_title, expected in [
                ("GrantRequest", "grant_request"),
                ("User", "user"),
                ("ThreePartName", "three_part_name")]:
            output = self.view.get_normalized_title(raw_title)
            self.assertEqual(output, expected)
