
# Fluxx Exporter

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

3. **(Optional) Create a Virtual Environment**  
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

4. **Install Dependencies**  
   Install the required Python packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

5. **Apply Migrations**  
   Apply the database migrations to set up the database schema:
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser**  
   Create a superuser to access the Django admin interface:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server**  
   Start the Django development server:
   ```bash
   python manage.py runserver
   ```
   Open your web browser and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to access the application.

## Configure the Environment

1. Navigate to [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).
2. Log in with the created superuser.
3. Here, you can configure your Fluxx instance and Amazon S3 instance.
4. You can also manually add and/or edit your Fluxx Entities and associate Columns with their respective entities in
   this interface.
   - The recommended approach to creating Entities and Columns is to use the built-in management command (see below).
   - Any changes to Entities or Columns will appear immediately upon refreshing the Fluxx Exporter Tool.
   - To configure related entities, select the option to relate the current entity to previous ones during setup. Note that the entity you are relating to must already be initialized.
   - There is no validation for entered entities or fields as per the Fluxx API. The correct names can be obtained from the API documentation (included in the Documentation folder) or by exporting an entity and checking the CSV output header.

## Importing Entities and Columns from Fluxx Glossary File

Entities and Columns can be imported from a Fluxx Glossary CSV file. To do this, run the management command from the project root:
```bash
python manage.py import_csv {/path/to/file.csv}
```

## Logging

This application logs to the console (stdout) as well as a file. Logging level and log file location can be configured
with the `LOG_FILE`, `FILE_LOG_LEVEL` and `CONSOLE_LOG_LEVEL` settings in `config.py`.


## License

This code is released under an MIT License. See `LICENSE` for more information.

## Funding

Support for the development of this application was generously provided by the Carnegie Corporation and the Ford Foundation.
