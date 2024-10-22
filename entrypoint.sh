#!/bin/bash

# Apply database migrations
echo "Creating config file"

if [ ! -f manage.py ]; then
  cd fluxx_exporter
fi

if [ ! -f fluxx_exporter/config.py ]; then
    cp fluxx_exporter/config.py.example fluxx_exporter/config.py
fi

echo "Apply database migrations"
python manage.py migrate

echo "Starting server"
python manage.py runserver 0.0.0.0:${APPLICATION_PORT}
