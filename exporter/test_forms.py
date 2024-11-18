from django.core.exceptions import ValidationError
from django.test import TestCase

from .forms import ExportJobWithTables, TableFieldFormset


class FormTests(TestCase):

    fixtures = ['initial.json']

    def setUp(self):
        self.form_data = {
            'name': 'asdfa',
            'fluxx_config': '1',
            'export_location': 'asdf',
            'export_format': 'json',
            'table_set-TOTAL_FORMS': '1',
            'table_set-INITIAL_FORMS': '1',
            'table_set-MIN_NUM_FORMS': '0',
            'table_set-MAX_NUM_FORMS': '1000',
            'table_set-0-id': '1',
            'table_set-0-include_in_export': 'on',
            'tablefield-table_set-0-field_set-TOTAL_FORMS': '4',
            'tablefield-table_set-0-field_set-INITIAL_FORMS': '4',
            'tablefield-table_set-0-field_set-MIN_NUM_FORMS': '0',
            'tablefield-table_set-0-field_set-MAX_NUM_FORMS': '1000',
            'tablefield-table_set-0-field_set-0-id': '2391',
            'tablefield-table_set-0-field_set-0-include_in_export': 'on',
            'tablefield-table_set-0-field_set-1-id': '2392',
            'tablefield-table_set-0-field_set-2-id': '2393',
            'tablefield-table_set-0-field_set-3-id': '2394',
        }

    def test_custom_formset(self):
        """Assert creation of nested forms and custom validation."""

        form = ExportJobWithTables(data=self.form_data)
        form.clean()
        for f in form.forms:
            self.assertIsInstance(f.nested, TableFieldFormset)

        self.form_data.pop('tablefield-table_set-0-field_set-0-include_in_export')
        form = ExportJobWithTables(data=self.form_data)
        with self.assertRaises(ValidationError) as err:
            form.clean()
        self.assertEqual(err.exception.message, 'You must add at least one field to this table.')

        self.form_data.pop('table_set-0-include_in_export')
        self.form_data['tablefield-table_set-0-field_set-0-include_in_export'] = 'on'
        form = ExportJobWithTables(data=self.form_data)
        with self.assertRaises(ValidationError) as err:
            form.clean()
        self.assertEqual(err.exception.message, 'You cannot export fields without also exporting the parent table.')
