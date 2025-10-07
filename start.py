# This script starts the compiled Fluxx Exporter application.
# In development, entrypoint.sh is targeted instead.

import os
import webbrowser

from django.core.management import execute_from_command_line

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fluxx_exporter.settings")


def migrate_db():
    execute_from_command_line(["manage.py", "migrate"])


def run_server():
    execute_from_command_line(["manage.py", "runserver", "--noreload"])


if __name__ == "__main__":
    print("Starting Fluxx Exporter")
    migrate_db()
    webbrowser.open("http://localhost:8000")
    run_server()
