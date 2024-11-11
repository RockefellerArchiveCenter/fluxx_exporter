import csv
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
    def test_csv(self, file_path):
        with open(file_path, newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                if row[0] == 'Fluxx Glossary':
                    return True
                else:
                    return False

    def is_field(self, row):
        return "field" in row[3].lower()

    def handle(self, *args, **options):

        with open(options['file_path'], newline='') as csvfile:
            if not self.test_csv(options['file_path']):
                print("File does not appear to be a Fluxx glossary csv.")
                exit()

            csvreader = csv.reader(csvfile)

            # this creates two lists; one of all the Entities, and one of all the Entities and Columns. Both formatted with the Entities formatted lower case and with underscores
            entities_list = []
            columns_list = []

            for row in filter(self.is_field, csvreader):
                columns_list.append([row[0].lower().replace(" ", "_"), row[1]])
                if row[0].lower().replace(" ", "_") not in entities_list:
                    entities_list.append(row[0].lower().replace(" ", "_"))

            # write entities to db
            for item in entities_list:
                Entity.objects.create(name=item)

            # write columns to database
            for item in columns_list:
                Column.objects.create(name=item[1], entity=Entity.objects.get(name=item[0]))
