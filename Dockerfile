FROM python:3.9-slim-buster
WORKDIR /nexfon-rspsrv
COPY ./sources.list /etc/apt/sources.list
RUN apt update && \
##apt upgrade -y && \
apt install tar libmagic-dev build-essential gettext libxrender-dev wget gcc ffmpeg make vim libmariadb-dev libmariadbclient-dev libffi-dev -y && \
pip install pipenv && \
wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz && \
tar -xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz && \
mv wkhtmltox/bin/wkhtmlto* /usr/bin/ && \
ln -nfs /usr/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf && \
rm -rf /var/lib/apt/lists/*
COPY ./Pipfile /nexfon-rspsrv
RUN pipenv update
COPY . /nexfon-rspsrv
EXPOSE 8000
ENTRYPOINT ["pipenv", "run", "uwsgi", "--ini", "./docker/configs/uwsgi/uwsgi.ini"]
