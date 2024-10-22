FROM python:3.10

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  && echo 'slapd/root_password password password' | debconf-set-selections \
  && echo 'slapd/root_password_again password password' | debconf-set-selections \
  && DEBIAN_FRONTEND=noninteractive apt-get -y install sudo \
    rsync \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt
ADD . /code/
