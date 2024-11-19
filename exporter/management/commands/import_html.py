import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from exporter.models import Field, Table


class Command(BaseCommand):
    help = "This command imports Fields and Tables from a directory of Fluxx API HTML documents."

    def add_arguments(self, parser):
        """Adds required directory argument"""
        parser.add_argument('directory', type=Path)

    def get_table_data(self, file_path):
        """Parses HTML file and returns table data.

        Args:
            file_path (pathlib.Path): path to HTML file.

        Returns:
            table_data (dict): Parsed table data.
        """
        try:
            with open(file_path, 'r') as html:
                doc = BeautifulSoup(html, features="html.parser")
                table = doc.find("table")
                rows = table.findAll('tr')
                headers = [th.text.strip() for th in rows[0].findAll('th')]
                table_data = []
                for row in rows[1:]:
                    parsed_row = [td.text.strip().rstrip('*') for td in row.findAll('td')]
                    row_dict = {}
                    for idx, key in enumerate(headers):
                        row_dict[key] = parsed_row[idx]
                    table_data.append(row_dict)
                return table_data
        except Exception as e:
            raise Exception(f'Encountered error when parsing data from {file_path}: {e}')

    def row_is_relation(self, row):
        """Determine if row represents a related table

        Args:
            row (dict): row of data from table.

        Returns:
            is_relation (bool): row represents database relation.
        """
        return bool(row['type'] == 'relation' and row['related_class'])

    def row_is_field(self, row):
        """Determine if row represents a field

        Args:
            row (dict): row of data from table.

        Returns:
            is_relation (bool): row represents field.
        """
        return bool(row['type'] and row['type'] != 'relation')

    def parse_related_table_name(self, row):
        """Generate normalized table name.

        Args:
            row (dict): row of data from table.

        Returns:
            parsed (str): parsed related table name.
        """
        parsed = re.findall('[A-Z][^A-Z]*', row['related_class'])
        return "_".join([s.lower() for s in parsed])

    def handle_row(self, row, table, directory, resolve=True):
        """Recursivey process rows, adding related entities.

        Args:
            row (dict): row of HTML table.
            table (Table instance): parent table with which Fields are associated.
            directory (str): path of directory containing HTML files.
            resolve (bool): resolve related tables.
        """
        if self.row_is_relation(row) and resolve:
            related_table_name = self.parse_related_table_name(row)
            related_table_docpath = Path(directory, f'{related_table_name}.html')
            if related_table_docpath.exists():
                related_table_data = self.get_table_data(related_table_docpath)
                related_table, _ = Table.objects.get_or_create(name=related_table_name)
                logging.debug(f"Table {related_table_name} created.")
                Field.objects.get_or_create(name=row['name'], table=table, related_table=related_table)
                logging.debug(f"Field {row['name']} created.")
                for row in related_table_data:
                    self.handle_row(row, related_table, directory, resolve=False)  # Relations are only resolved one level deep
            else:
                logging.info(f"Could not import table {related_table_name} because {related_table_docpath} does not exist.")
        elif self.row_is_field(row):
            Field.objects.get_or_create(name=row['name'], table=table)
            logging.debug(f"Field {row['name']} created.")

    def handle(self, *args, **options):
        """Main method to import Tables and Fields from HTML Fluxx API doc page."""
        logging.debug(f"Importing Tables and Fields from HTML files in {options['directory']}")
        grant_request_data = self.get_table_data(Path(options['directory'], 'grant_request.html'))
        table, _ = Table.objects.get_or_create(name='grant_request', export_job=None)
        logging.debug("Table grant_request created.")
        for row in grant_request_data:
            self.handle_row(row, table, options['directory'])
        logging.debug("Import from HTML data complete.")
