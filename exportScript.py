import boto3
from botocore.exceptions import NoCredentialsError
import csv
import json
import os
import paramiko
import pysftp
import requests
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from fetchConfigDetails import fetch_fluxx_configs, fetch_sftp_configs, fetch_s3_configs

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluxxBuild.settings')
django.setup()

'''def main():
    # Check if command-line arguments are passed
    if len(sys.argv) > 1:
        # Extract inputs from command-line arguments
        inputs = sys.argv[1:]
        
        # Get format value, filter value, and output folder path from the arguments
        output_folder = inputs.pop() if inputs else ""
        format_value = inputs.pop() if inputs else ""
        filter_value = inputs.pop() if inputs else ""
        
        # Parse the remaining inputs for entity and column data
        inputs = parse_data(inputs)
        
        # Initialize the Fluxx connection
        fluxx = Fluxx()
'''
def main():
    # Check if command-line arguments are passed
    if len(sys.argv) > 1:
        # Extract inputs from command-line arguments
        inputs = sys.argv[1:]
        
        # Print inputs for debugging
        print(f"Command-line arguments: {inputs}")

        # Get format value, filter value, and output folder path from the arguments
        output_folder = inputs.pop() if inputs else ""
        format_value = inputs.pop() if inputs else ""
        filter_value = inputs.pop() if inputs else ""

        # Print extracted values for debugging
        print(f"Output folder: {output_folder}")
        print(f"Format value: {format_value}")
        print(f"Filter value: {filter_value}")

        # Parse the remaining inputs for entity and column data
        inputs = parse_data(inputs)
        
        # Print parsed data for debugging
        print(f"Parsed entities and columns: {inputs}")

        # Initialize the Fluxx connection
        fluxx = Fluxx()
        # Iterate over each entity and process its data
        for entity_data in inputs:
            entity = str(entity_data[0]).lower()
            columns = entity_data[1:]
            
            # Parse and handle filter value
            filter_value = parse_filter(filter_value)
            
            # Fetch rows for the entity with the specified columns and filter
            listEntityElements = fluxx.list_rows(entity, columns, filter=filter_value)
            
            try:
                # Process and export the fetched data
                results = listEntityElements.json()['records']
                localDataExport(entity, results, fluxx, int(format_value), output_folder)
            except Exception as e:
                print(f"Error retrieving list of records. Entity: {entity} containing columns: {columns} did not return a response from the API: {e}")
                pass

            # Send data over SFTP
            try:
                if fetch_sftp_configs('SFTP Test'):
                    host, username, password, remotedir = fetch_sftp_configs('SFTP Config')
                    send_directory_over_sftp(host, username, password, output_folder, remotedir)
            except Exception as e:
                print(f"Exception while retrieving SFTP configuration: {e}")
                pass

            # Upload data to S3 bucket
            try:
                if fetch_s3_configs('S3 Config'):
                    bucket, access_key, secret_key = fetch_s3_configs('S3 Config')
                    upload_directory_to_s3(output_folder, bucket, access_key, secret_key)
            except Exception as e:
                print(f"Exception while retrieving Amazon S3 Bucket configuration: {e}")
                pass

    else:
        print("No data received.")


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


def parse_filter(filter_value):
    print(f"Raw filter value: '{filter_value}'")  # Debug output

    if filter_value:
        filter_parts = filter_value.split(' ', 2)  # Split only at the first two spaces
        if len(filter_parts) != 3:
            raise ValueError("Filter format must be 'field operator value'")
        return filter_parts
    else:
        return None  # No filter provided


def localDataExport(entity, json_data, fluxx, format, output_folder):
    try:
        # Create the output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Create entity-specific subfolder
        entity_folder_path = os.path.join(output_folder, entity)
        if not os.path.exists(entity_folder_path):
            os.makedirs(entity_folder_path)

        # Function to write JSON file
        def write_json(record, sub_folder_path):
            json_file_path = os.path.join(sub_folder_path, f'{entity}-{record["id"]}.json')
            with open(json_file_path, 'w') as json_file:
                json.dump(record, json_file, indent=4)

        # Function to write XML file
        def write_xml(record, sub_folder_path):
            xml_file_path = os.path.join(sub_folder_path, f'{entity}-{record["id"]}.xml')
            root = ET.Element(entity)
            for key, value in record.items():
                child = ET.SubElement(root, key)
                child.text = str(value)
            tree = ET.ElementTree(root)
            tree.write(xml_file_path)

        # Function to write CSV file
        def write_csv(record, sub_folder_path):
            csv_file_path = os.path.join(sub_folder_path, f'{entity}-{record["id"]}.csv')
            with open(csv_file_path, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(record.keys())  # Write headers
                writer.writerow(record.values())  # Write data

        # Dictionary to mimic switch statements for format handling
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
                # Create sub-folder for each record under the entity-specific folder
                sub_folder_path = os.path.join(entity_folder_path, f"grant_request_{record_id}")
                
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


def sftp_put_dir(sftp, local_dir, remote_dir):
    # Normalize the local directory path
    local_dir = os.path.normpath(local_dir)
    
    # Create remote directory if it does not exist
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass  # Assume directory already exists

    # Recursively upload files and directories
    for root, dirs, files in os.walk(local_dir):
        
        # Calculate the relative path from the local directory
        rel_path = os.path.relpath(root, local_dir)
        remote_path = os.path.join(remote_dir, rel_path).replace('\\', '/')
        
        for dir_name in dirs:
            remote_subdir = os.path.join(remote_path, dir_name).replace('\\', '/')
            try:
                sftp.mkdir(remote_subdir)
            except IOError:
                pass 
        
        for file_name in files:
            local_file = os.path.join(root, file_name)
            remote_file = os.path.join(remote_path, file_name).replace('\\', '/')
            sftp.put(local_file, remote_file)
            print(f"Uploaded {local_file} to {remote_file}")

def send_directory_over_sftp(hostname, username, password, local_dir, remote_dir):
    try:
        # Create an SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the server on port 22 (SFTP)
        ssh.connect(hostname, port=22, username=username, password=password)
        
        # Create an SFTP session from the SSH connection
        sftp = ssh.open_sftp()
        
        # Upload the directory recursively
        sftp_put_dir(sftp, local_dir, remote_dir)
        
        # Close the SFTP session and SSH connection
        sftp.close()
        ssh.close()
        
        print(f"Directory {local_dir} successfully uploaded to {remote_dir}")
    except Exception as e:
        print(f"Error occurred: {e}")


def upload_directory_to_s3(directory, bucket, access_key, secret_key):
    print(f"directory: {directory}")
    """Upload all files in the specified directory to an S3 bucket
    
    :param directory: Directory containing files to upload
    :param bucket: Bucket to upload to
    :param access_key: AWS Access Key ID
    :param secret_key: AWS Secret Access Key
    :return: None
    """
    # Get the current date in mmddyyyy format
    current_date = datetime.now().strftime('%m%d%Y')
    
    # Create an S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    
    # List all files in the directory
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            # Create the object key with the date folder and subdirectory structure
            relative_path = os.path.relpath(file_path, directory)
            object_name = f"{current_date}/{relative_path}".replace("\\", "/")
            try:
                # Upload the file
                s3_client.upload_file(file_path, bucket, object_name)
                print(f"{file_name} has been uploaded to {bucket}/{object_name}")
            except NoCredentialsError:
                print("Credentials not available")
            except Exception as e:
                print(f"Failed to upload {file_name} to {bucket}: {e}")




class Fluxx(object):
    '''Fluxx object that will handle connection/session and subsequent requests'''
    
    version = 'v2'

    def __init__(self, config_name='Armanino Demo'):
        #get config information from DB
        instance_domain, application_id, secret = fetch_fluxx_configs(config_name)

        #Optional style parameter, generally best kept as 'Full'
        style = 'full'
        
        #concat domain and extension onto API request/not accounting for Pre-production environments (can be added)
        domain = 'fluxx'
        extension = 'io'
        
        #create base URL for fluxx
        fluxx_url = f'https://{instance_domain}.{domain}.{extension}/'
        
        #generate token
        token_url = fluxx_url + 'oauth/token'
        
        #oauth parameters to retrieve token
        oauth_params = {
            'grant_type': 'client_credentials',
            'client_id': application_id,
            'client_secret': secret
            }

        #begin a Request Session
        self.session = requests.Session()
        
        #obtain oauth token
        try:
            response = self.session.post(token_url, data=oauth_params)
        except:
            print("No response from client API")
            
        #Set Session request headers to persist connection
        try:
            self.token = response.json()['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
                })
        except:
            print("Could not find access token")
            
        self.api_url = fluxx_url + 'api/rest/v2/'
        

    def list_rows(self, entity, columns, page=1, per_page=100, filter=None):
        '''Function to return a list of some number of rows and pages relating to an entinty (or table)
        Filters can be applied following the format: <entity> <logic> <condition>
        Example: amount_requested eq 10000
        Filters can be tied together as follows: amount_requested eq 10000 and created_at today
        Filter logic will be requested and further documented at a later date
        '''       

        if page < 1:
            raise ValueError("Page integer must be greater than 0.")      

        list_params = {
            'cols': json.dumps(columns),
            'page': page,
            'per_page': per_page
            }

        if filter: 
            list_params.update({
                'filter':json.dumps(filter)
            })
        
        return self.session.get(self.api_url+entity, params=list_params)


    def download_document(self, document_id, sub_folder_path):
        document_id = str(document_id)
        download_params = {
            'cols': json.dumps(["document_file_name"])
        }
        #get the filename and type
        document_info = self.session.get(self.api_url + 'model_document/' + document_id, params=download_params)
        document_name = document_info.json()['model_document']['document_file_name']
        
        #get the file and save to respective folder
        document_download_url = self.api_url + 'model_document_download/' + document_id
        response = self.session.get(document_download_url, stream=True)
        
        with open(os.path.join(sub_folder_path, document_name), 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)


if __name__ == '__main__':
    main()
