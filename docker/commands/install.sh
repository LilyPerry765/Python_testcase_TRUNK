#!/bin/bash
pipenv run python manage.py compilemessages  && \
pipenv run python manage.py makemigrations && \
pipenv run python manage.py migrate --database=default && \
pipenv run python manage.py migrate --database=cdr_db && \
pipenv run python manage.py loaddata groups && \
pipenv run python manage.py collectstatic --noinput  && \
pipenv run python manage.py createsuperuser && \
echo "RSPSRV installed successfully"
