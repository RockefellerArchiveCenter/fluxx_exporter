import csv
import json
import logging
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from pathvalidate import sanitize_filename

from .clients import AmazonS3Client, FluxxClient
from .models import ExportJob

logging = logging.getLogger(__name__)


class Exporter(object):
    """Main class which exports data and binary documents."""

    def __init__(self, export_job_id):
        """Sets attribute from the export job

        Args:
            export_job_id (int): Database id for an ExportJob instance
        """
        try:
            export_job = ExportJob.objects.get(pk=export_job_id)
            self.fluxx_config = export_job.fluxx_config
            self.filters = export_job.filters.all()
            self.grant_ids = export_job.grant_ids
            self.export_format = export_job.export_format
            self.export_location = export_job.export_location
            self.amazon_s3_config = export_job.amazon_s3_config
            self.sftp_config = export_job.sftp_config
            self.grant_request_table = export_job.grant_request_table
        except ObjectDoesNotExist:
            logging.error(f"Could not find export job configuration for id {export_job_id}.")
            raise Exception(f"Could not find export job configuration for id {export_job_id}.")

        self.export_path = Path(self.export_location)
        self.export_path.mkdir(exist_ok=True, parents=True)

    def fluxx_export(self):
        """Exports data and documents from a Fluxx instance."""
        logging.info('Fluxx export started')
        try:
            fluxx_client = FluxxClient(
                self.fluxx_config.base_url,
                self.fluxx_config.client_id,
                self.fluxx_config.client_secret)

            logging.debug('Exporting data for grant_request table')

            filter_value = self.parse_filter(self.filters)
            grant_ids = self.parse_grant_ids(self.grant_ids)
            field_names = self.parse_field_names(self.grant_request_table)
            relations = self.parse_related_fields(self.grant_request_table)
            results = fluxx_client.list_rows(
                'grant_request',
                field_names,
                filter_value=filter_value,
                grant_ids=grant_ids,
                relations=relations)
            logging.debug('Returned results for grant_request table from Fluxx.')

            logging.info('Saving data exported from Fluxx.')
            for record in results:
                logging.debug(f'Saving data for record {record["id"]}')
                record_path = (self.export_path / f"grant_request_{str(record['id'])}")
                record_path.mkdir()
                try:
                    self.save_data(record, self.export_format, record_path)
                except Exception as e:
                    logging.error(f'Error exporting {self.export_format} to {str(record_path)}: {e}')
                    raise Exception(f'Error exporting {self.export_format} to {str(record_path)}: {e}')
                for doc_id in record.get('model_documents', []):
                    logging.debug(f'Downloading document {doc_id}')
                    file_name, file_obj = fluxx_client.download_document(doc_id)
                    sanitized_file_name = sanitize_filename(str(file_name))
                    logging.debug(f'Saving document {doc_id} with file name {sanitized_file_name}')
                    self.save_document(sanitized_file_name, file_obj, record_path)

                if self.amazon_s3_config:
                    logging.info('Uploading to S3')
                    try:
                        s3_client = AmazonS3Client(
                            self.amazon_s3_config.bucket,
                            self.amazon_s3_config.access_key_id,
                            self.amazon_s3_config.secret_key,
                            self.amazon_s3_config.region,)
                        s3_client.upload_directory(record_path)
                    except Exception as e:
                        logging.error(f'Error uploading to S3 bucket {self.amazon_s3_config.bucket}: {e}')
                        raise Exception(f'Error uploading to S3 bucket {self.amazon_s3_config.bucket}: {e}')

            logging.info('Fluxx export complete.')
            return True, None
        except Exception as err:
            logging.error(''.join(traceback.format_exception(err)))
            tb = '<br/>'.join(traceback.format_exception(err)[:-1])
            return False, f'<b>{str(err)}</b><br/><br/>{tb}'

    def parse_field_names(self, table):
        """Return field names to export

        Args:
            table (Table instance): parent Table containing fields.

        Returns:
            fields (list of str): names of fields to export.
        """
        default_fields = ['model_documents']
        return default_fields + [c.name for c in table.fields.filter(include_in_export=True)]

    def parse_filter(self, filters):
        """Formats filters.

        Args:
            filter (list): Filter objects.

        Returns:
            filter_parts (list or dict): parsed filter.
        """
        logging.debug(f'Parsing filters {filters}')
        filter_value = None
        if filters:
            filter_list = []
            for f in filters:
                filter_list.append([f.field_name, f.relator, f.value])
            if len(filter_list) > 1:
                filter_value = {"group_type": "and", "conditions": filter_list}
            else:
                filter_value = filter_list[0]

        logging.debug(f'Filter {filters} parsed into parts {filter_value}')
        return filter_value

    def parse_grant_ids(self, grant_ids):
        """Split a string of Grant IDs into a list.

        Args:
            grant_ids (str): comma-separated list of grant ids.

        Returns:
            grant_id_list (list): list of grant ids.
        """
        return [g.strip() for g in grant_ids.split(',')] if grant_ids else None

    def parse_related_fields(self, table):
        """Structures related tables request parameter.

        Args:
            related_tables (list of Table instances): list of related tables.

        Returns:
            relation_params (dict): structured relationship parameter.
        """
        logging.debug(f'Parsing related tables for fields in {table.name}')
        relation_params = {}
        for field in table.fields.filter(include_in_export=True, related_table__isnull=False):
            related_fields = [field.name for field in field.related_table.fields.filter(include_in_export=True)]
            relation_params[field.name] = related_fields
            logging.debug(f'Params for fields {related_fields} in related table {field.related_table.name} added.')
        logging.debug(f'Related tables for {table.name} parsed to params {relation_params}')
        return relation_params

    def save_data(self, json_data, export_format, export_location):
        """Saves exported data to export location.

        Args:
            json_data (dict): data to be saved.
            export_format (str): format in which data should be saved.
            export_location (pathlib.Path): location in which data should be saved.
        """
        getattr(self, f"write_{export_format}")(json_data, export_location)

    def save_document(self, file_name, file_stream, export_location):
        """Saves document as binary file.

        Args:
            file_name (str): Name of file to be saved.
            file_stream: Streaming file response from HTTP
            export_location (pathlib.Path): location in which documents should be saved.
        """
        with open((export_location / file_name), 'wb') as fp:
            for chunk in file_stream.iter_content(chunk_size=8192):
                fp.write(chunk)

    def write_json(self, record, export_location):
        """Writes data as JSON.

        Args:
            record (dict): data that should be saved.
            export_location (pathlib.Path): location in which data should be saved.
        """
        json_file_path = Path(export_location, f'{record["id"]}.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(record, json_file, indent=4)

    def write_xml(self, record, export_location):
        """Writes data as XML.

        Args:
            record (dict): data that should be saved.
            export_location (pathlib.Path): location in which data should be saved.
        """
        xml_file_path = Path(export_location, f'{record["id"]}.xml')
        root = ET.Element(record["id"])
        for key, value in record.items():
            child = ET.SubElement(root, key)
            child.text = str(value)
        tree = ET.ElementTree(root)
        tree.write(xml_file_path)

    def write_csv(self, record, export_location):
        """Writes data as CSV.

        Args:
            record (dict): data that should be saved.
            export_location (pathlib.Path): location in which data should be saved.
        """
        csv_file_path = Path(export_location, f'{record["id"]}.csv')
        with open(csv_file_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(record.keys())  # Write headers
            writer.writerow(record.values())  # Write data
