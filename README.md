# Fluxx Exporter

The Fluxx Exporter is an open-source tool that integrates with the grants management system [Fluxx](https://www.fluxx.io/) for the purposes of automating exports of select elements of grant records. The tool is built on Python and Django, and uses the Fluxx API to export data from a configured Fluxx instance. It can export both structured data that is entered into fields and stored in the database as well as files that are uploaded and attached to the grant record.

Foundations use grants management systems (GMS) such as Fluxx to manage their grant making from the time a grantee begins an application, through the award process, and on to the grantees’ final reporting on activities. For most foundations, the GMS is the permanent system of record for all grant-related records. Foundation archivists have struggled to find scalable solutions for exporting closed grant records from these systems. This tool allows archivists to select and export grant information, for long-term preservation and researcher access. 

## Installation

1. Download the package for your operating system (Windows, MacOS or Linux) from the [releases page](https://github.com/RockefellerArchiveCenter/fluxx_exporter/releases). Choose the most recent release version.
2. Extract the downloaded ZIP file.
3. Run the application: double-click the `fluxx_exporter` file in the folder you just extracted, and a terminal window will open that shows the application starting.
4. Follow the prompt in the terminal to enter a username and password for a superuser. You will **only** be prompted to create login credentials the **first time** you start Fluxx Exporter. Save the username and password for future logins.
5. Access Fluxx Exporter in your browser. The Fluxx Exporter home page will automatically open in your default browser when the application starts, but you can access it in any browser at [http://localhost:8000](http://localhost:8000).
6. To close the application, close the terminal window that opened when you double-clicked on the `fluxx_exporter` application file.

You will notice that a file called `fluxx_exporter_db.sqlite3` is created in your home directory (`C:\Users\{username}` on Windows and `/Users/{username}` on Mac). This file stores all of the Fluxx configurations, users, fields, tables and export 
jobs that you configure for the application, so do not delete it unless you want to wipe all that information. 

## Configuration

1. Navigate to [http://localhost:8000/admin](http://localhost:8000/admin).
2. Log in with the superuser username and password you created during installation.
3. [Configure your Fluxx instance](#configuring-a-fluxx-instance)
4. If desired, [add credentials for an Amazon S3 Bucket](#configuring-an-amazon-s3-bucket).
5. Configure the app to [recognize the tables and fields in your Fluxx instance](#configuring-tables-and-fields).

### Configuring a Fluxx Instance

#### Acquiring Fluxx Credentials

**You must have Fluxx administrator access to perform these steps.**

In order for the Fluxx Exporter tool to be able to access your Fluxx instance, you need to authorize the app and create a Client ID and Client Secret:

1. Log into Fluxx and navigate to this page: {fluxx-instance-base-url}/oauth/applications/
2. Click "New Application" in the Fluxx interface.
3. Name the new application (e.g. Fluxx Exporter).
4. Copy your Fluxx instance's base URL into the redirect URI.
5. Leave Scopes field blank.
6. Press "Submit."
7. You should receive an application ID and secret on the following page. Save these in a safe place.
8. Click "Authorize" to complete the creation of Fluxx API Credentials.

#### Creating a Fluxx Configuration

On the Fluxx Exporter admin page, under "Site Administration", click on "Fluxx configs" and then the "Add Fluxx Config" button. Enter the credentials you created in Fluxx in the fields provided, along with a descriptive name for the Fluxx instance. You can configure additional Fluxx instances if desired.


### Configuring an Amazon S3 Bucket
On the Fluxx Exporter admin page, under "Site Administration", click on "Amazon s3 configs" and then the "Add Amazon S3 Config" button. Enter the bucket name, credentials, and region in the fields provided, along with a descriptive name for the S# instance. You can configure additional S3 instances if desired.


### Configuring Tables and Fields

The recommended approach to creating tables and fields is to use the upload form to import data from Fluxx API documentation.

#### Downloading API Documentation Pages

**You must have Fluxx administrator access to perform these steps.**

Your Fluxx instance's built-in API documentation is available at {fluxx-instance-base-url}/api/rest/v2/doc. For each table you wish to export from Fluxx, download the documentation page to a local folder.

#### Uploading pages
In Fluxx Exporter, navigate to the [Import](http://localhost:8000/import/) page, and then upload all the documentation pages you want to import.

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
Fluxx API filters allow users to export only records that meet certain criteria. Filters in Fluxx Exporter consist of three parts separated by a pipe character (`|`): 

1. Field name
2. Relator
3. Value

Filter examples:

| Description                                  | Filter Syntax                                 |
|----------------------------------------------|-----------------------------------------------|
| Grant ID equal to `R-2024-00003`             | `grant_id\|eq\|R-2024-00003`                  |
| Project Title equal to `Test Project`        | `project_title\|eq\|Test Project`             |
| Grant record created in the last five months | `created_at\|last-n-months\|5`                |
| Grant record created in the last year*        | `created_at\|this-year\|-`                   |
| Only closed grants                           | `state\|eq\|closed`                           |
| Grants closed within a range of years        | `\grant_closed_at\|range-year-cal\|2010-2024` |

\* Note: In the filter `"created_at|this-year|-"`, the hyphen (`-`) is not a typo. This is how the Fluxx API handles filters with fewer than three raw inputs.

For more information about filters:
- Consult your Fluxx instance's built-in API pages at {fluxx-instance-base-url}/api/rest/v2/doc to see which filters will work for a given table. 
- Consult the official Fluxx API documentation. This is not publicly available, but if your institution has access, it contains more information about filters in the "API Filter Examples" section.

## Logging

This application logs to the console (stdout) as well as a file. Logging level and log file location can be configured
with the `LOG_FILE`, `FILE_LOG_LEVEL` and `CONSOLE_LOG_LEVEL` settings in `config.py`.

## User Management

This application currently does not require authentication, however the Django Administration site (which allows configuration of Fluxx instances and S3 buckets) requires a login from a user with admin access. In the steps above, the superuser account that is created will provide access to this interface.

## Contributing

This is an open source project and we welcome contributions! If you want to fix a bug, or have an idea of how to enhance the application, the process looks like this:

1. File an issue in this repository. This will provide a location to discuss proposed implementations of fixes or enhancements, and can then be tied to a subsequent pull request.
2. If you have an idea of how to fix the bug (or make the improvements), fork the repository and work in your own branch. When you are done, push the branch back to this repository and set up a pull request. Automated unit tests are run on all pull requests. Any new code should have unit test coverage, documentation (if necessary), and should conform to the Python PEP8 style guidelines.
3. After some back and forth between you and core committers (or individuals who have privileges to commit to the base branch of this repository), your code will probably be merged, perhaps with some minor changes.

This repository contains a configuration file for git [pre-commit](https://pre-commit.com/) hooks which help ensure that code is linted before it is checked into version control. It is strongly recommended that you install these hooks locally by installing pre-commit and running `pre-commit install`.

## License

This code is released under an MIT License. See `LICENSE` for more information.

## Funding

Support for the development of this application was generously provided by the Carnegie Corporation and the Ford Foundation.
