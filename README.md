
# Fluxx Exporter

The Fluxx Exporter is an open-source tool that integrates with the grants management system [Fluxx](https://www.fluxx.io/) for the purposes of automating exports of select elements of grant records. The tool is built on Python and Django, and uses the Fluxx API to export data from a configured Fluxx instance. It can export both structured data that is entered into fields and stored in the database as well as files that are uploaded and attached to the grant record.

Foundations use grants management systems (GMS) such as Fluxx to manage their grant making from the time a grantee begins an application, through the award process, and on to the grantees’ final reporting on activities. For most foundations, the GMS is the permanent system of record for all grant-related records. Foundation archivists have struggled to find scalable solutions for exporting closed grant records from these systems. This tool allows archivists to select and export grant information, for long-term preservation and researcher access. 

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1. **Python**: Python 3.11. You can download it from [python.org](https://www.python.org/downloads/).
2. **Git**: Git must be installed. Download it from [git-scm.com](https://git-scm.com/downloads).

## Installation

Follow these steps to set up the Fluxx Exporter:

1. **Clone the Repository**  
   Open your terminal and clone the repository using Git:
   ```bash
   git clone https://github.com/RockefellerArchiveCenter/fluxx_exporter.git
   ```

2. **Navigate into the Cloned Directory**  
   Change into the directory:
   ```bash
   cd fluxx_exporter
   ```

3. **Create Config File**  
   Create a config file from the template:
   ```bash
   cp fluxx_exporter/config.py.example fluxx_exporter/config.py
   ```

4. **Start the application**
   You can run the application using the supplied Docker container, which we recommend. If you are not able to use Docker, 
   additional steps must be taken to create a local environment in which the application can run. 

   **Using Docker**
   
   If you have [Docker](https://www.docker.com/products/docker-desktop/) installed, you can bring the application up by running:
   ```bash
   docker compose up
   ```
   Open your web browser and navigate to [http://localost:8000](http://localost:8000) to access the application.

   **Using a local environment**
   1. Create a virtual environment to manage dependencies:
   ```bash
   python -m venv venv
   ```
   2. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

   3. Install the required Python packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

   4. Apply the database migrations to set up the database schema:
   ```bash
   python manage.py migrate
   ```

   5. Start the Django development server:
   ```bash
   python manage.py runserver
   ```
   Open your web browser and navigate to [http://localost:8000](http://localost:8000) to access the application.

5. **Create a Superuser**  
   Create a superuser to access the Django admin interface:
   If you're using the Docker container, enter the following command in a new terminal window:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```
   
   If you're running the application in your local environment, enter the following command
   in a new terminal window from the application's root directory:
   ```bash
   python manage.py createsuperuser
   ```

   

## Configuration

1. Navigate to [http://localost:8000/admin](http://localost:8000/admin).
2. Log in with the created superuser.
3. [Configure your Fluxx instance](#configuring-a-fluxx-instance)
4. If desired, [add credentials for an Amazon S3 Bucket](#configuring-an-amazon-s3-bucket).
4. Configure the app to [recognize the tables and fields in your Fluxx instance](#configuring-tables-and-fields).

### Configuring a Fluxx Instance

#### Acquiring Fluxx Credentials

**You must have Fluxx administrator access to perform these steps.**

In order for the Fluxx Exporter tool to be able to access your Fluxx instance, you need to authorize the app and create a Client ID and Client Secret:

1. Log into Fluxx and navigate to this page: https://{your-fluxx-instance}.fluxx.io/oauth/applications/

2. Click "New Application" in the Fluxx interface.
3. Name the new application (e.g. Fluxx Exporter).
3. Copy your Fluxx instance's URL into the redirect URI (e.g. https://{your-fluxx-instance}.fluxx.io).
4. Leave Scopes field blank.
5. Press "Submit." You should receive an application ID and secret on the following page. Save these in a safe place. 

#### Creating a Fluxx Configuration

On the Fluxx Exporter admin page, under "Site Administration", click on "Fluxx configs" and then the "Add Fluxx Config" button. Enter the credentials you created in Fluxx in the fields provided, along with a descriptive name for the Fluxx instance. You can configure additional Fluxx instances if desired.


### Configuring an Amazon S3 Bucket
On the Fluxx Exporter admin page, under "Site Administration", click on "Amazon s3 configs" and then the "Add Amazon S3 Config" button. Enter the bucket name, credentials, and region in the fields provided, along with a descriptive name for the S# instance. You can configure additional S3 instances if desired.


### Configuring Tables and Fields

The recommended approach to creating tables and fields is to use the built-in management command to import data from Fluxx API documentation.

#### Downloading API Documentation Pages

**You must have Fluxx administrator access to perform these steps.**

Your Fluxx instance's built-in API documentation is available at https://{your-fluxx-instance}.fluxx.io/api/rest/v2/doc. For each table you wish to export from Fluxx, download the documentation page to a local folder, using the table's normalized name as a filename. For example, the GrantRequest table docs, located at: https://{your-fluxx-instance}.fluxx.io/api/rest/v2/GrantRequest/doc would be saved as `grant_request.html`. Save all downloaded docs in the same local folder.

#### Running the management command

In a terminal window, navigate to the application root. If you are running the application in a Docker container, execute the management command, targeting the running container:
```bash
docker compose exec web python manage.py import_html {/path/to/directory/with/html/files}
```

If you are not using Docker, you can execute the command directly:
```bash
python manage.py import_html {/path/to/directory/with/html/files}
```

#### Manually adding or editing tables and fields
You can also manually add and/or edit your Fluxx tables and associate fields with their respective tables in the admin interface.
   - Any changes to tables or fields will appear immediately upon refreshing the Fluxx Exporter Tool.
   - To configure related tables, select the option to relate the current table to previous ones during setup. Note that the table you are relating to must already be initialized.
   - There is no validation for entered tables or fields as per the Fluxx API. The correct names can be obtained from the API documentation or by exporting a table from the Fluxx UI and checking the CSV output header.

## Exporting Grants

Once the app is fully configured, navigate to [http://localhost:8000](http://localhost:8000). From this page you can create an export job, which can then be run on demand.

### Creating Export Jobs
Export jobs require at minimum:
- Name
- Fluxx configuration
- Local export location
- Export format
- The tables and fields you want to export

Optionally, if you wish to upload exported records to an Amazon S3 bucket, you can add an Amazon S3 configuration. 

There are two options available for filtering which records you want to export:
- A comma-separated list of grant IDs to export.
- A filter that is applied to grant records (see [Filters](#filters) below.)

#### Filters
Fluxx API filters generally consist of three parts, for example:

   - "grant_id eq R-2024-00003"  
   - "project_title eq Test Project"
   - "created_at last-n-months 5"
   - "created_at this-year -"

Note that in the last filter ('created_at this-year -'), the last input of the hyphen is not a typo. This is how the Fluxx API handles less than 3 raw inputs into the filter. 

Consult your Fluxx instance's built-in API pages at https://{your-fluxx-instance}.fluxx.io/api/rest/v2/doc to see which filters will work for a given table. Official Fluxx API documentation, which is not publicly available, contains   more information is available in the "API Filter Examples" section.

## Logging

This application logs to the console (stdout) as well as a file. Logging level and log file location can be configured
with the `LOG_FILE`, `FILE_LOG_LEVEL` and `CONSOLE_LOG_LEVEL` settings in `config.py`.

## User Management

This application currently does not require authentication, however the Django Administration site (which allows configuration of Fluxx instances and S3 buckets) requires a login from a user with admin access. In the steps above, the superuser account that is created will provide access to this interface.


## License

This code is released under an MIT License. See `LICENSE` for more information.

## Funding

Support for the development of this application was generously provided by the Carnegie Corporation and the Ford Foundation.
