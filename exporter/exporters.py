import csv
import json
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist

from .clients import FluxxClient, S3Client
from .models import ExportJob

# TODO replace prints with logging


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
            self.filter_string = export_job.filter_string
            self.export_format = export_job.export_format
            self.export_location = export_job.export_location
            self.s3_config = export_job.s3_config
            self.sftp_config = export_job.sftp_config
            self.entities = export_job.entity_set.all()
        except ObjectDoesNotExist:
            raise Exception(f"Could not find export job configuration for id {export_job_id}.")

        self.export_path = Path(self.export_location)
        self.export_path.mkdir(exist_ok=True, parents=True)

    def fluxx_export(self):
        """Exports data and documents from a Fluxx instance."""
        try:
            fluxx_client = FluxxClient(
                self.fluxx_config.base_url,
                self.fluxx_config.client_id,
                self.fluxx_config.client_secret)

            for entity in self.entities:
                entity_path = (self.export_path / entity.name)
                entity_path.mkdir(exist_ok=True)

                filter_value = self.parse_filter(self.filter_string)
                related_entity = self.parse_related_entities(entity.related_entities.all())
                results = fluxx_client.list_rows(
                    entity.name,
                    [c.name for c in entity.column_set.all()],
                    filter_value=filter_value,
                    related_entity=related_entity)

                for record in results:
                    record_path = (entity_path / str(record['id']))
                    record_path.mkdir()
                    self.save_data(record, self.export_format, record_path)
                    for doc_id in record.get('model_documents', []):
                        file_name, file_obj = fluxx_client.download_document(doc_id)
                        self.save_document(file_name, file_obj, record_path)

                    if self.s3_config:
                        try:
                            s3_client = S3Client(
                                self.s3_config.bucket,
                                self.s3_config.access_key_id,
                                self.s3_config.secret_key,
                                self.s3_config.region,)
                            s3_client.upload_directory(record_path)
                        except Exception as e:
                            # TODO raise meaniungful exception
                            print(
                                f"Exception while retrieving Amazon S3 Bucket configuration: {e}")
                            pass
            return True, None
        except Exception as err:
            tb = '<br/>'.join(traceback.format_exception(err)[:-1])
            return False, f'<b>{str(err)}</b><br/><br/>{tb}'

    def parse_filter(self, filter):
        """Split the filter string into components.

        If the filter does not have exactly three parts it is not used.

        Args:
            filter (str): Filter string to be parsed.

        Returns:
            filter_parts (list): parsed filter.
        """
        filter_parts = None
        if filter:
            try:
                filter_parts = filter.split(' ', 2)
                assert len(filter_parts) == 3
            except AssertionError:
                raise Exception(f"Could not parse filter value {filter}")

        return filter_parts

    def parse_related_entities(self, related_entities):
        """Structures related entities request parameter.

        Args:
            related_entities (list of Entity instances): list of related entities.

        Returns:
            relation_params (dict): structured relationship parameter.
        """
        relation_params = {}
        for related_entity in related_entities:
            re_columns = [column.name for column in related_entity.column_set.all()]
            relation_params[related_entity.name] = re_columns
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
