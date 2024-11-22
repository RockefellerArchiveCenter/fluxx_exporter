
# Fluxx Exporter

## About

The Fluxx Exporter is an open-source tool that integrates with the grants management system [Fluxx](https://www.fluxx.io/) for the purposes of automating exports of select elements of grant records. The tool is built on Python and Django, and uses the Fluxx API to export data from a configured Fluxx instance. It can export both structured data that is entered into fields and stored in the database as well as files that are uploaded and attached to the grant record.

Foundations use grants management systems (GMS) such as Fluxx to manage their grant making from the time a grantee begins an application, through the award process, and on to the grantees’ final reporting on activities. For most foundations, the GMS is the permanent system of record for all grant-related records. Foundation archivists have struggled to find scalable solutions for exporting closed grant records from these systems. This tool allows archivists to select and export grant information, for long-term preservation and researcher access. 

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1. **Python**: Python 3.6 or higher. You can download it from [python.org](https://www.python.org/downloads/).
2. **Git**: Git must be installed. Download it from [git-scm.com](https://git-scm.com/downloads).

## Installation and Configuration Steps

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

4. **Start app with Docker**
   If you have [Docker](https://www.docker.com/products/docker-desktop/) installed, 
   you can bring the application up by running:
   ```bash
   docker compose up
   ```
   If you don't have Docker installed, follow steps 4a-4d below. Otherwise skip 
   to step 5.

4a. **(Optional) Create a Virtual Environment**  
   It's recommended to create a virtual environment to manage dependencies:
   ```bash
   python -m venv venv
   ```
   Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4b. **Install Dependencies**  
   Install the required Python packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

4c. **Apply Migrations**  
   Apply the database migrations to set up the database schema:
   ```bash
   python manage.py migrate
   ```

4d. **Run the Development Server**  
   Start the Django development server:
   ```bash
   python manage.py runserver
   ```
   Open your web browser and navigate to [http://localost:8000](http://localost:8000) to access the application.

5. **Create a Superuser**  
   Create a superuser to access the Django admin interface:
   ```bash
   python manage.py createsuperuser
   ```

## Configure the Environment

1. Navigate to [http://localost:8000/admin](http://localost:8000/admin).
2. Log in with the created superuser.
3. Configure your Fluxx instance ([see below for obtaining API credentials](#Authorizing-the-tool-with-your-Fluxx-instance-and-creating-the-Client-ID-and-Secret)) and Amazon S3 instance.
4. Configure the app to recognize the tables and fields in your Fluxx instance. Use the built-in management command (preferred) or  do so manually from the admin panel. See [Importing Tables and Fields](#Importing-Tables-and-Fields) below for more information.

## Authorize the tool with your Fluxx instance and create the Client ID and Secret

**NB: **You must have Fluxx administrator access to perform these steps.**

In order for the Fluxx Exporter tool to be able to access your Fluxx instance, you need to authorize the app and create a Client ID and Client Secret.

Log into Fluxx and navigate to this page: https://{yourfluxxinstance}.fluxx.io/oauth/applications/

Click "New Application," name the authorization (e.g. Fluxx Exporter), copy your Fluxx instance's URL into the redirect URI (e.g. https://{yourfluxxinstance}.fluxx.io), and leave Scopes blank.  Press "Submit." You should receive an application ID and secret on the following page.  Save these in a safe place. Navigate to the app's admin panel, and enter the newly created credentials there.

If you have access to the Fluxx API documentation, see the file "4 Getting Started with Fluxx APIs.pdf".

## Importing Tables and Fields

The recommended approach to creating tables and fields is to use the built-in management command and the Fluxx Glossary Report CSV. The Fluxx Glossary Report CSV file can be downloaded from the Live Reports tab in Fluxx. Run the management command from the project root:
```bash
python manage.py import_csv {/path/to/file.csv}
```
You can also manually add and/or edit your Fluxx tables and associate fields with their respective tables in the admin interface.
   - Any changes to tables or fields will appear immediately upon refreshing the Fluxx Exporter Tool.
   - To configure related tables, select the option to relate the current table to previous ones during setup. Note that the table you are relating to must already be initialized.
   - There is no validation for entered tables or fields as per the Fluxx API. The correct names can be obtained from the API documentation (included in the Documentation folder) or by exporting a table and checking the CSV output header.

Tables and fields can also be found in your Fluxx instance's built-in API documentation: https://{your-fluxx-instance}.fluxx.io/api/rest/v2/doc. For example, if there is a table named GrantRequest, the fields can be found here: https://{your-fluxx-instance}.fluxx.io/api/rest/v2/GrantRequest/doc

## Running the Export

Once the app is fully configured, navigate to [http://localost:8000](http://localost:8000). From this page you can configure your export to run, with records selected either as a list of grant IDs or as a filtered search. Some sample filter queries:

   - "grant_id eq R-2024-00003"  
   - "project_title eq Test Project"
   - "created_at last-n-months 5"
   - "created_at this-year -"

Note that in the last filter ('created_at this-year -'), the last input of the hyphen is not a typo. This is how the Fluxx API handles less than 3 raw inputs into the filter. It is best to consult your Fluxx instance's built-in API pages to see which filters will work for a given table, which are around at: https://{your-fluxx-instance}.fluxx.io/api/rest/v2/doc

If you have access to the Fluxx API documentation, see also the file "6.1 API Filter Examples.pdf".

## Logging

This application logs to the console (stdout) as well as a file. Logging level and log file location can be configured
with the `LOG_FILE`, `FILE_LOG_LEVEL` and `CONSOLE_LOG_LEVEL` settings in `config.py`.


## License

This code is released under an MIT License. See `LICENSE` for more information.

## Funding

Support for the development of this application was generously provided by the Carnegie Corporation and the Ford Foundation.
