import csv
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from exporter.models import Field, Table


class Command(BaseCommand):
    help = "This command imports a Fluxx Glossary Report CSV file and generates corresponding Fields and Tables."

    def add_arguments(self, parser):
        """Adds required file_path argument"""
        parser.add_argument('file_path', type=Path)

    def test_csv(self, csvreader):
        """Checks to make sure the CSV file has the string `Fluxx Glossary` in A1"""
        return list(csvreader)[0][0] == 'Fluxx Glossary'

    def is_field(self, row):
        """Return boolean indication of whether row represents a field."""
        return "field" in row[3].lower()

    def handle(self, *args, **options):

        with open(options['file_path'], newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            if not self.test_csv(csvreader):
                logging.error(f"File {options['file_path']} does not appear to be a Fluxx glossary csv.")
                raise Exception(f"File {options['file_path']} does not appear to be a Fluxx glossary csv.")

            csvfile.seek(0)  # reset read position to beginning of file

            for row in filter(self.is_field, csvreader):
                table_name = row[0].lower().replace(" ", "_")
                table, _ = Table.objects.get_or_create(name=table_name)
                Field.objects.get_or_create(name=row[1], table=table)
