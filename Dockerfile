FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Install Python requirements
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY exporter fluxx_exporter entrypoint.sh manage.py ./