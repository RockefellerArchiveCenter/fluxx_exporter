from unittest.mock import patch

from django.contrib.messages import ERROR, SUCCESS, get_messages
from django.test import TestCase
from django.urls import reverse

from .forms import ExportJobWithEntities
from .models import Column, Entity, ExportJob


class ViewTests(TestCase):

    fixtures = ['views.json']

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

        export_job = ExportJob.objects.all().first()
        response = self.client.get(reverse('exportjob_update', kwargs={'pk': export_job.pk}))
        self.assertIsInstance(response.context['formset'], ExportJobWithEntities)

        initial_entities = Entity.objects.all().count()
        initial_columns = Column.objects.all().count()
        response = self.client.post(reverse('exportjob_update', kwargs={'pk': export_job.pk}), self.form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Entity.objects.all().count(), initial_entities)
        self.assertEqual(Column.objects.all().count(), initial_columns)

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
