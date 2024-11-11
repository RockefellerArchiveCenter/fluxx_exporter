import csv
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from exporter.models import Column as Column
from exporter.models import Entity as Entity


class Command(BaseCommand):
    help = "This command imports a fluxx entity csv and creates columns and entities from the Fluxx glossary csv file. The syntax is python manage.py input_csv path/to/filename"

    # require filename to be passed as an argument
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=Path)

    # test for the attribute of Fluxx glossary csv having Fluxx Glossary in A1
    def test_csv(self, csvreader):
        return list(csvreader)[0][0] == 'Fluxx Glossary'

    def is_field(self, row):
        return "field" in row[3].lower()

    def handle(self, *args, **options):

        with open(options['file_path'], newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            if not self.test_csv(csvreader):
                logging.error(f"File {options['file_path']} does not appear to be a Fluxx glossary csv.")
                raise Exception(f"File {options['file_path']} does not appear to be a Fluxx glossary csv.")

            csvfile.seek(0)  # reset read position to beginning of file

            for row in filter(self.is_field, csvreader):
                entity_name = row[0].lower().replace(" ", "_")
                entity, _ = Entity.objects.get_or_create(name=entity_name)
                Column.objects.get_or_create(name=row[1], entity=entity)
