from django.core.management.base import BaseCommand

from exporter.exporters import Exporter


class Command(BaseCommand):
    help = "Exports data from Fluxx."

    def add_arguments(self, parser):
        parser.add_argument('export_job', type=int, help='ID of the export job to use for configurations.')

    def handle(self, *args, **options):
        try:
            Exporter(options['export_job']).fluxx_export()
        except Exception as e:
            raise Exception("Error exporting data from Fluxx.") from e
