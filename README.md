# Fluxx Exporter Documentation

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Configure a Fluxx Instance](#configure-a-fluxx-instance)
  - [Configure an Amazon S3 Bucket (Optional)](#configure-an-amazon-s3-bucket-optional)
  - [Configure Fluxx Tables and Fields](#configure-fluxx-tables-and-fields)
- [Export Grant Records](#export-grant-records)
  - [Create Export Jobs](#create-export-jobs)
  - [Add Filters](#add-filters)
- [Logging](#logging)
- [User Management](#user-management)
- [Contributing](#contributing)
- [License](#license)
- [Funding](#funding)

## Overview
The Fluxx Exporter is an open-source tool that integrates with the grants management system [Fluxx](https://www.fluxx.io/) to automate exports of select elements of grant records. The tool is built with Python and Django, and uses the Fluxx API to export data from a configured Fluxx instance. It can export both structured data from Fluxx database fields and files that are attached to grant records.

Foundations use grants management systems (GMS) such as Fluxx to manage their grant making from the time a grantee begins an application, through the award process, and on to the grantee's final reporting on activities. For most foundations, the GMS is the permanent system of record for all grant-related records. This tool allows grants administrators, information managers, and archivists to select and export grant information for internal or external uses including for long-term preservation, researcher access, and organizational learning and evaluation.

## Installation

**Warning messages will appear when the current version of Fluxx Exporter (2.0) is run on Windows or MacOS. Speak to your local system administrator for information about how to resolve these warnings.**

1. [Download the latest release](https://github.com/RockefellerArchiveCenter/fluxx_exporter/releases) for your operating system (Windows, MacOS or Linux).
2. Extract the downloaded ZIP file.
3. Run the application: double-click the `fluxx_exporter` file in the folder you just extracted, and a terminal window will open that shows the application starting.
4. Enter a superuser username and password in the terminal when prompted. You will **only** be prompted to create login credentials the **first time** you start Fluxx Exporter. Save the username and password for future logins.
5. The app will open automatically in your browser at [http://localhost:8000](http://localhost:8000).
6. To close, exit the terminal window.

Note: Two files are created as siblings of the `fluxx_exporter` file. The file called `fluxx_exporter_db.sqlite3` stores 
the Fluxx configurations, users, fields, tables, and export jobs that you configure for the application, so do not delete it unless you want to remove that information. The file called `fluxx_exporter.debug.log` contains a detailed log of system
activity and is useful for in-depth troubleshooting. If you move the `fluxx_exporter` file to a new location, you should 
move these files to that same location.

## Configuration

### Configure a Fluxx Instance

#### Step 1: Get Fluxx API Credentials

**Fluxx administrator access is required.**

In order for the Fluxx Exporter tool to be able to access your Fluxx instance, you need to authorize the app and create a Client ID and Client Secret:

1. Log into Fluxx and navigate to `{fluxx-instance-base-url}/oauth/applications/`
2. Click "New Application" in the Fluxx interface.
3. Enter an application name (e.g. Fluxx Exporter).
4. Copy your Fluxx base URL into the redirect URI.
5. Leave Scopes field blank.
6. Press "Submit."
7. You should receive an application ID and secret on the following page. Save these in a safe place.
8. Click "Authorize" to complete the creation of Fluxx API Credentials.

#### Step 2: Add API Credentials in Fluxx Exporter

1. In Fluxx Exporter, navigate to the [Configurations page](http://localhost:8000/configurations/) and select the option to create a new Fluxx Configuration
2. Enter a descriptive name and the credentials you created in Fluxx

You can configure multiple Fluxx instances as needed.

### Configure an Amazon S3 Bucket (Optional)

1. In Fluxx Exporter, navigate to the [Configurations page](http://localhost:8000/configurations/) and select the option to create a new Amazon S3 Configuration
2. Enter a descriptive name, S3 bucket name, and AWS credentials

You can configure additional S3 instances as needed.

### Import Fluxx Tables and Fields

Fluxx tables and fields are the backend database information that power Fluxx cards on the frontend. Fluxx Exporter uses these tables and their associated fields to allow you to customize what information to export. 

#### Step 1: Download Fluxx Table API Documentation Pages

**Fluxx administrator access is required.**

1. Go to `{fluxx-instance-base-url}/api/rest/v2/doc` to access the API documentation for your Fluxx instance.
2. From the list of API documentation links, click "GrantRequest".
3. Save this grant request table documentation webpage as an HTML file on your computer.
4. Repeat this process for all Fluxx tables that contain data you would like to export, saving each HTML documentation file for use by Fluxx Exporter.

Note: You can explore the existing tables and their associated fields in `{fluxx-instance-base-url}/api/rest/v2/doc` to determine what data and fields you want to be able to export from Fluxx.

#### Step 2: Upload Fluxx Table API Documentation Pages
Fluxx Exporter requires information from your API documentation to configure tables and fields for export. Follow these steps to import the HTML files you just downloaded from Fluxx.

1. In Fluxx Exporter, navigate to the [Import page](http://localhost:8000/import/)
2. Use the form to select the grant request HTML file that you downloaded from Fluxx (required), and any other table documentation files you downloaded.
3. Click "Upload" to import these files.

## Export Grant Records

Once the configuration is complete, navigate to [Fluxx Exporter](http://localhost:8000) to create and run export jobs.

### Create Export Jobs
Each export job requires:
- Job name
- Fluxx configuration
- Export location
- Export format
- Selected tables and the specific fields from each you want to include in the export

Optionally, include:
- A comma-separated list of specific grant IDs to export
- A filter that limits which grant records to export (see [Add Filters](#add-filters) below)
- Amazon S3 configuration
- An indication of which document versions to download
- Selected document types you wish to download

#### Add Filters
Fluxx API filters allow users to export only records that meet certain criteria. Filters in Fluxx Exporter consist of three parts: 

1. Field name
2. Relator
3. Value

Filter examples:

| Description                                  | Filter Syntax                                 |
|----------------------------------------------|-----------------------------------------------|
| Grant ID equal to `R-2024-00003`             | `grant_id eq R-2024-00003`                  |
| Project Title equal to `Test Project`        | `project_title eq Test Project`             |
| Grant record created in the last five months | `created_at last-n-months 5`                |
| Grant record created in the last year*       | `created_at this-year -`                    |
| Only closed grants                           | `state eq closed`                           |
| Grants closed within a range of years        | `grant_closed_at range-year-cal 2010-2024` |
| Grants closed in a specific year             | `grant_closed_at range 01/01/2020-12/31/2020` |
| Grants approved in a specific year           | `grant_approved_at range 01/01/2020-12/31/2020` |

\* Note: In the filter `"created_at this-year -"`, the hyphen (`-`) is not a typo. This is how the Fluxx API handles filters with fewer than three raw inputs.

For more information about filters:
- Consult your Fluxx instance's built-in API pages at `{fluxx-instance-base-url}/api/rest/v2/doc` to see which filters will work for a given table. 
- Consult the official Fluxx API documentation. This is not publicly available, but if your institution has access, it contains more information about filters in the "API Filter Examples" section.

## Logging

This application logs to the console (stdout) as well as a file. By default, messages in the console are logged at the
`INFO` level, while file logging logs all messages included in the `DEBUG` level to a file called `fluxx_exporter.debug.log`
that is a sibling of the application executable. The logging level and log file name can be configured with the `FILE_LOG_LEVEL`, `CONSOLE_LOG_LEVEL` and `LOG_FILE` settings in `config.py`.

## Contributing

This is an open source project and we welcome contributions! If you want to fix a bug, or have an idea of how to enhance the application, the process looks like this:

1. File an issue in this repository. This will provide a location to discuss proposed implementations of fixes or enhancements, and can then be tied to a subsequent pull request.
2. If you have an idea of how to fix the bug (or make the improvements), fork the repository and work in your own branch. When you are done, push the branch back to this repository and set up a pull request. Automated unit tests are run on all pull requests. Any new code should have unit test coverage, documentation (if necessary), and should conform to the Python PEP8 style guidelines.
3. After some back and forth between you and core committers (or individuals who have privileges to commit to the base branch of this repository), your code will probably be merged, perhaps with some minor changes.

This repository contains a configuration file for git [pre-commit](https://pre-commit.com/) hooks which help ensure that code is linted before it is checked into version control. It is strongly recommended that you install these hooks locally by installing pre-commit and running `pre-commit install`.

## Local Development

In order to support local development, a Dockerfile and Docker Compose file are included. To use these, install [git](https://git-scm.com/) and [Docker](https://www.docker.com/get-started/), and then follow the instructions below.

Open your terminal and clone the repository using git:

    $ git clone git@github.com:RockefellerArchiveCenter/fluxx_exporter

Move to the root directory of the repository:

    cd fluxx_exporter

Start the app with Docker Compose:

    $ docker compose up

Once the application starts successfully, you should be able to access it in your browser at `http://localhost:8000`

## License

This code is released under an MIT License. See `LICENSE` for more information.

## Funding

Support for the development of this application was generously provided by the Carnegie Corporation and the Ford Foundation.
