from django.core.exceptions import ValidationError
from django.test import TestCase

from .forms import EntityColumnFormset, ExportJobWithEntities


class FormTests(TestCase):

    fixtures = ['initial.json']

    def setUp(self):
        self.form_data = {
            'name': 'asdfa',
            'fluxx_config': '1',
            'export_location': 'asdf',
            'export_format': 'json',
            'entity_set-TOTAL_FORMS': '1',
            'entity_set-INITIAL_FORMS': '1',
            'entity_set-MIN_NUM_FORMS': '0',
            'entity_set-MAX_NUM_FORMS': '1000',
            'entity_set-0-id': '1',
            'entity_set-0-include_in_export': 'on',
            'column_set-TOTAL_FORMS': '1',
            'column_set-INITIAL_FORMS': '1',
            'column_set-MIN_NUM_FORMS': '0',
            'column_set-MAX_NUM_FORMS': '1000',
            'column_set-0-id': '1',
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
