#!/bin/bash
pipenv run python manage.py compilemessages && \
pipenv run python manage.py makemigrations && \
pipenv run python manage.py migrate --database=default && \
pipenv run python manage.py migrate --database=cdr_db  && \
echo "RSPSRV updated successfully"
