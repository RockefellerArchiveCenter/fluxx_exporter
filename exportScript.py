import csv
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

import django

from exporter.clients import FluxxClient, S3Client, SFTPClient

django.setup()

# import pysftp


def main():
    # Check if command-line arguments are passed
    if len(sys.argv) > 1:
        # Print the passed through data
        print("Data received in exportScript.py:", sys.argv[1:])

        inputs = sys.argv[1:]
        # print(f"inputs: {inputs}")
        # Get last values from argv and set to format,filter values,
        # respectively
        related_entities = []
        while inputs[-1] not in ["1", "2", "3"]:
            # inputs.pop() if inputs else ""
            related_entities.append(inputs.pop()if inputs else None)

        format_value = inputs.pop() if inputs else ""
        filter_value = inputs.pop() if inputs else ""
        print(f"inputs: {inputs}")
        inputs = parse_data(inputs)
        print(f"inputs: {inputs}")
        fluxx = FluxxClient()

        for entity_data in inputs:
            local_dir = os.path.join(os.getcwd(), datetime.now().strftime("%m%d%Y"))  # TODO fix this
            entity = str(entity_data[0]).lower()
            print(f"Entity: {entity}")
            columns = entity_data[1:]
            print(f"columns: {columns}")
            filter_value = parse_filter(filter_value)
            print(f"filters: {filter_value}")
            related_entity = parse_related_entity(related_entities, entity)
            listEntityElements = fluxx.list_rows(
                entity, columns, filter=filter_value, related_entity=related_entity)
            # print(f"list elements: {listEntityElements.json()}")
            try:
                results = listEntityElements.json()['records']
                # print(results)
                localDataExport(entity, results, fluxx, int(format_value))
            except Exception:
                print(
                    f"Except while retrieving list of records. Entity: {entity} containing columns: {columns} did not return a response from the API")
                pass

            # TODO these should actually be conditionals based on export job
            # send over sftp
            try:
                sftp_client = SFTPClient()
                sftp_client.put_directory(local_dir)
                sftp_client.close()
            except Exception as e:
                print(f"Exception while retrieving SFTP configuration: {e}")
                pass

            # send to S3 bucket
            try:
                s3_client = S3Client()
                s3_client.upload_directory(local_dir)
            except Exception as e:
                print(
                    f"Exception while retrieving Amazon S3 Bucket configuration: {e}")
                pass

    else:
        print("No data received.")


def parse_related_entity(related_entity_list, entity):
    # Loop through the related entity list
    for related_entity in related_entity_list:
        if len(related_entity) != 0:
            # Split the entity and related entity by '|'
            related_entity_parts = related_entity.split('|', 1)
            print(f"related_entity_parts: {related_entity_parts}")
            # Ensure the split gives us exactly two parts
            # (entity|relatedentity)
            if len(related_entity_parts) == 2:
                entity_part, related_entity_part = related_entity_parts

                # Check if the entity matches the first part
                if entity_part == entity:
                    print(
                        f"Matching entity found, related entity: {related_entity_part}")
                    return related_entity_part  # Return the related entity

    # If no match is found, return an empty string
    return ""


def parse_data(input_data):
    entity_columns = {}

    for item in input_data:
        if '|' in item:
            entity, column = item.split('|', 1)
            if entity not in entity_columns:
                entity_columns[entity] = []
            entity_columns[entity].append(column)
        else:
            print(f"Invalid item: {item}")

    # Format the data into two separate lists
    entities_with_columns = []
    for entity, cols in entity_columns.items():
        entities_with_columns.append([entity] + cols)

    return entities_with_columns


def parse_filter(filter):
    if (len(filter) != 0):
        # Split the filter string into components
        # split only at the first two spaces
        filter_parts = filter.split(' ', 2)

        # Ensure that we got exactly three parts
        if len(filter_parts) != 3:
            raise ValueError("Filter format must be 'field operator value'")
    else:
        filter_parts = ""

    # Return the parts as a list
    return filter_parts


def localDataExport(entity, json_data, fluxx, format):
    try:
        # Get current date in mmddyyyy format
        current_date = datetime.now().strftime("%m%d%Y")

        # Create top-level folder with current date
        top_level_folder_name = current_date
        top_level_folder_path = os.path.join(
            os.getcwd(), top_level_folder_name)

        # Create top-level folder if it doesn't exist
        if not os.path.exists(top_level_folder_path):
            os.makedirs(top_level_folder_path)

        # Function to write JSON file
        def write_json(record, sub_folder_path):
            json_file_path = os.path.join(
                sub_folder_path, f'{entity}-{record["id"]}.json')
            with open(json_file_path, 'w') as json_file:
                json.dump(record, json_file, indent=4)

        # Function to write XML file
        def write_xml(record, sub_folder_path):
            xml_file_path = os.path.join(
                sub_folder_path, f'{entity}-{record["id"]}.xml')
            root = ET.Element(entity)
            for key, value in record.items():
                child = ET.SubElement(root, key)
                child.text = str(value)
            tree = ET.ElementTree(root)
            tree.write(xml_file_path)

        # Function to write CSV file
        def write_csv(record, sub_folder_path):
            csv_file_path = os.path.join(
                sub_folder_path, f'{entity}-{record["id"]}.csv')
            with open(csv_file_path, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(record.keys())  # Write headers
                writer.writerow(record.values())  # Write data

        # Dictionary to mimic switch statements because I like them better than
        # nested IFs
        format_handlers = {
            1: write_json,
            2: write_xml,
            3: write_csv
        }

        # Get the appropriate handler function based on the format
        handler = format_handlers.get(format)

        # Iterate through each record in the entity data
        for record in json_data[entity]:
            record_id = record.get('id')
            if record_id is not None:
                # Create sub-folder for each record under top-level folder
                sub_folder_name = f"{entity}_data"
                sub_folder_path = os.path.join(
                    top_level_folder_path,
                    sub_folder_name,
                    f"grant_request_{record_id}")

                if not os.path.exists(sub_folder_path):
                    os.makedirs(sub_folder_path)

                # Call the appropriate handler function based on the format
                if handler:
                    handler(record, sub_folder_path)

                # Download additional documents if available
                if record.get('model_documents'):
                    for doc_id in record.get('model_documents'):
                        fluxx.download_document(doc_id, sub_folder_path)

        return True
    except Exception as e:
        print(f"Error creating folders and files for entity '{entity}': {e}")
        return False


if __name__ == "__main__":
    main()
