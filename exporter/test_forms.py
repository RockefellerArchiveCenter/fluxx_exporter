from django.test import TestCase

from .forms import ExportJobWithTables, TableFieldFormset


class FormTests(TestCase):

    fixtures = ['initial.json']

    def setUp(self):
        self.form_data = {
            'name': 'Export Job',
            'fluxx_config': '1',
            'export_location': '/tmp/exports',
            'export_format': 'json',
            'filter_string': '',
            'grant_ids': '1,2,3,4',
            'amazon_s3_config': '1',
            'table_set-TOTAL_FORMS': '2',
            'table_set-INITIAL_FORMS': '2',
            'table_set-MIN_NUM_FORMS': '0',
            'table_set-MAX_NUM_FORMS': '1000',
            'table_set-0-id': '2',
            'table_set-0-include_in_export': 'on',
            'table_set-0-name': 'grant_request',
            'tablefield-table_set-0-fields-TOTAL_FORMS': '1',
            'tablefield-table_set-0-fields-INITIAL_FORMS': '1',
            'tablefield-table_set-0-fields-MIN_NUM_FORMS': '0',
            'tablefield-table_set-0-fields-MAX_NUM_FORMS': '1000',
            'tablefield-table_set-0-fields-0-id': '2',
            'tablefield-table_set-0-fields-0-include_in_export': 'on',
            'table_set-1-id': '3',
            'table_set-1-include_in_export': 'on',
            'table_set-1-name': 'grant_request',
            'tablefield-table_set-1-fields-TOTAL_FORMS': '1',
            'tablefield-table_set-1-fields-INITIAL_FORMS': '1',
            'tablefield-table_set-1-fields-MIN_NUM_FORMS': '0',
            'tablefield-table_set-1-fields-MAX_NUM_FORMS': '1000',
            'tablefield-table_set-1-fields-0-id': '3',
            'tablefield-table_set-1-fields-0-include_in_export': 'on',
        }

    def test_custom_formset(self):
        """Assert creation of nested forms and custom validation."""

        form = ExportJobWithTables(data=self.form_data)
        form.clean()
        for f in form.forms:
            self.assertIsInstance(f.nested, TableFieldFormset)

        self.form_data.pop('tablefield-table_set-0-fields-0-include_in_export')
        form = ExportJobWithTables(data=self.form_data)
        form.clean()
        self.assertIn('You must add at least one field to this table.', form.errors[0]['__all__'])
