
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

5. **Configuration**  
   Configure the `exportScript.py` (Fluxx class) with your API credentials:
   - `api_url`
   - `client_id`
   - `client_secret`
   
   Alternatively, you can configure the script to use environment variables, a YAML file, or a similar approach.

6. **Apply Migrations**  
   Apply the database migrations to set up the database schema:
   ```bash
   python manage.py migrate
   ```

7. **Create a Superuser**  
   Create a superuser to access the Django admin interface:
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the Development Server**  
   Start the Django development server:
   ```bash
   python manage.py runserver
   ```
   Open your web browser and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to access the application.

## Configure the Environment

1. Navigate to [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).
2. Log in with the created superuser.
3. Here, you can configure your Fluxx instance, SFTP instance, and Amazon S3 instance.
4. You can also add your Fluxx entities and associate Columns with their respective entities.
   - Any changes to Entities or Columns will appear immediately upon refreshing the Fluxx Exporter Tool.
   - To configure related entities, select the option to relate the current entity to previous ones during setup. Note that the entity you are relating to must already be initialized.
   - Currently, related entities will not appear in the UI, so ensure any columns/fields entered in the configuration page will be fed into the API via the relation parameter.
   - There is no validation for entered entities or fields as per the Fluxx API. The correct names can be obtained from the API documentation (included in the Documentation folder) or by exporting an entity and checking the CSV output header.

## License

Include license information if applicable.
