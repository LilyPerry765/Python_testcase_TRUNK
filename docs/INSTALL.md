# Installation

## Stop and disable firewalld 

**Important note:** if you use centOS please stop/disable firewalld and disable selinux

- `‍‍systemctl stop firewalld`
- `systemctl disable firewalld`

## Disable selinux
```
setenforce  0 ##### disable selinux from now to next reboot
SELINUX=disabled  ### default value is enforcing, change it to disabled ## disable after next reboot for all time
```

## Requirements

```bash
yum update -y
yum install -y centos-release-scl epel-release
yum install -y git wget vim gcc gcc-c++ devtoolset-8-gcc devtoolset-8-gcc-c++ make libXrender python3-devel openssl-devel mysql-devel yum-utils libodb-mysql-devel libsqlite3x-devel libffi-devel MariaDB-shared MariaDB-devel MariaDB-compat
scl enable devtoolset-8 -- bash
```


### Database

Install `mariadb` with this [link](https://mariadb.com/kb/en/yum/)

- Create databases and users:

```
CREATE DATABASE sbc_db;
CREATE USER 'sbc'@'localhost' IDENTIFIED BY 'sbcpw';
GRANT ALL PRIVILEGES ON sbc_db.* TO 'sbc'@'localhost' IDENTIFIED BY 'sbcpw'; 
GRANT ALL PRIVILEGES ON sbc_db.* TO 'sbc'@'%' IDENTIFIED BY 'sbcpw'; 
FLUSH PRIVILEGES;

CREATE DATABASE rspsrv_db CHARACTER SET utf8mb4 collate utf8mb4_general_ci;
CREATE USER 'rspsrv'@'localhost' IDENTIFIED BY 'sbcpw';
GRANT ALL PRIVILEGES ON rspsrv_db.* TO 'rspsrv'@'localhost' IDENTIFIED BY 'rspsrvpw'; 
GRANT ALL PRIVILEGES ON rspsrv_db.* TO 'rspsrv'@'%' IDENTIFIED BY 'rspsrvpw'; 
FLUSH PRIVILEGES;

CREATE DATABASE switch_db;
CREATE USER 'switch'@'localhost' IDENTIFIED BY 'switchpw';
GRANT ALL PRIVILEGES ON switch_db.* TO 'switch'@'localhost' IDENTIFIED BY 'switchpw'; 
GRANT ALL PRIVILEGES ON switch_db.* TO 'switch'@'%' IDENTIFIED BY 'switchpw'; 
FLUSH PRIVILEGES;

GRANT ALL PRIVILEGES ON sbc_db.* TO 'root'@'%' IDENTIFIED BY 'P@ssw0rd';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'P@ssw0rd';
FLUSH PRIVILEGES;
```

### Python

Download `python 3.9.0+` source.

```
wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tgz

#extract Python-3.9.0.tgz
tar -xzvf Python-3.9.0.tgz
cd Python-3.9.0

yum install gcc gcc-c++ make 
yum install -y openssl-devel

./configure --enable-optimizations
make altinstall   # if you have error in this stage==> install libssl and try again

pip3.9 install pipenv
```

### Install Redis

```
sudo yum install yum-utils
sudo yum install http://rpms.remirepo.net/enterprise/remi-release-7.rpm
sudo yum-config-manager --enable remi
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis
```

### WKHTMLTOPDF

Install `wkhtmltopdf 0.12.4 qt`

```
wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
tar xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
mv wkhtmltox/bin/wkhtmlto* /usr/bin/
ln -nfs /usr/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
```


### Ffmpeg 

```
sudo rpm -v --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-5.el7.nux.noarch.rpm
sudo yum install ffmpeg ffmpeg-devel
```

## Project setup

### Clone

```
cd /usr/local/src/
git clone -b  master git@git.respina.net:backend/rspsrv.git
mv rspsrv/rspsrv/settings/local.example.env  rspsrv/rspsrv/settings/local.env
```

### Install modules

```
cd /usr/local/src/rspsrv
pipenv install 
pipenv shell 
```

### Load groups

- `python manage.py loaddata groups`

### Initial setup

```
python manage.py compilemessages
python manage.py makemigrations
python manage.py migrate --database=default
python manage.py migrate --database=cdr_db
python manage.py createsuperuser
```

### Setup uWSGI

Create an `uwsgi.ini` file:

- `chdir` is the base directory of the project
- Create the directory of `logto` path

```
[uwsgi]
socket = :8000
# Django-related settings
# the base directory (full path)
chdir = /usr/local/src/rspsrv
# Django's wsgi file
module = rspsrv.wsgi
# Run as user
uid = root
pidfile = /var/run/rspsrv-uwsgi.pid
# master
master = true
# maximum number of worker processes
processes = 2
chmod-socket = 664
threaded-logger = true
logto = /var/log/rspsrv/uwsgi.log
log-maxsize = 10000000
logfile-chown = true
# clear environment on exit
vacuum = true
die-on-term = true
```

Create an `uwsgi_params` file (Needed in `nginx` setup):

```
uwsgi_param  QUERY_STRING       $query_string;
uwsgi_param  REQUEST_METHOD     $request_method;
uwsgi_param  CONTENT_TYPE       $content_type;
uwsgi_param  CONTENT_LENGTH     $content_length;

uwsgi_param  REQUEST_URI        $request_uri;
uwsgi_param  PATH_INFO          $document_uri;
uwsgi_param  DOCUMENT_ROOT      $document_root;
uwsgi_param  SERVER_PROTOCOL    $server_protocol;
uwsgi_param  REQUEST_SCHEME     $scheme;
uwsgi_param  HTTPS              $https if_not_empty;

uwsgi_param  REMOTE_ADDR        $remote_addr;
uwsgi_param  REMOTE_PORT        $remote_port;
uwsgi_param  SERVER_PORT        $server_port;
uwsgi_param  SERVER_NAME        $server_name;
```

### Static files

`python manage.py collectstatic`


### Run ARI

`python manage.py start_ari`

### Celery worker

To queue jobs there is one `Celery` worker named `rspsrv`, run it (or create a service for it) with this command within the project's virtual environment:

- `celery -A rspsrv worker -l info`

### Email and SMS templates

Use `rspsrv/prime` directory's full path from [here](https://git.respina.net/nexfon/notification-templates) in `RSPSRV_NOTIFICATION_TEMPLATE_PATH` local environment and run this command any time:

- `python manage.py load_templates`

Note that email and sms templates are loaded automatically on start, so use this command when you want to change templates with no down time.

### Sample `nginx` config 

Copy these lines to `/etc/nginx/conf.d/rspsrv.conf`

```
upstream rspsrv-uwsgi {
        server 127.0.0.1:8000;
}

server {
    listen 8080;
    server_name  _;

   # Send /api /payment and /admin requests to Django.
   location ~ ^(.*)/api/(.*)$|^/admin|^/payment {
        add_header 'Access-Control-Allow-Origin' '*';
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET,PATCH, POST, OPTIONS, PUT, DELETE' always;
            add_header 'Access-Control-Max-Age' 1728000 always;
            add_header 'Access-Control-Allow-Credentials' 'true';
            add_header 'Access-Control-Allow-Headers' '*' always;
            add_header 'Content-Type' 'text/plain; charset=utf-8' always;
            add_header 'Content-Length' 0 always;
            return 204;
        }
        if ($request_method = 'POST') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Credentials' 'true';
            add_header 'Access-Control-Allow-Methods' 'GET, POST,PATCH, OPTIONS, PUT, DELETE' always;
            add_header 'Access-Control-Allow-Headers' '*' always;
            add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        }
        if ($request_method = 'GET') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Credentials' 'true';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS,PATCH, PUT, DELETE' always;
            add_header 'Access-Control-Allow-Headers' '*' always;
            add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        }
        if ($request_method = 'PUT') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Credentials' 'true';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT,PATCH, DELETE' always;
            add_header 'Access-Control-Allow-Headers' '*' always;
            add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        }
        if ($request_method = 'DELETE') {
            add_header 'Access-Control-Allow-Credentials' 'true';
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, PATCH,DELETE' always;
            add_header 'Access-Control-Allow-Headers' '*' always;
            add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        }
        if ($request_method = 'PATCH') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Credentials' 'true';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, PATCH,DELETE' always;
            add_header 'Access-Control-Allow-Headers' '*' always;
            add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        }
       include /opt/rspsrv/uwsgi/uwsgi_params;
       uwsgi_pass  rspsrv-uwsgi;
   }

    # This should match with RSPSRV_STATIC_ROOT and RSPSRV_STATIC_URL
    location /static {
          alias /opt/rspsrv/collected_static;
    }

    # Send all non-media web-requests to the Django server.
    location ~ ^(.*)/web/(.*)$ {
        proxy_pass http://rspsrv-uwsgi;
    }
}
```

### Sample systemd

#### ARI controller

- vim /etc/systemd/system/`ari`.service


```bash
[Unit]
Description=Run ARI
After=network.target

[Service]
Type=simple
WorkingDirectory=/usr/local/src/rspsrv
EnvironmentFile=/usr/local/src/rspsrv/rspsrv/settings/local.env
ExecStart=/usr/local/bin/pipenv run python -u manage.py start_ari
StandardOutput=journal
#StandardOutput=append:/var/log/ari.log
#StandardError=append:/var/log/ari-error.log
StandardError=journal
SyslogIdentifier=arilogger
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### API

- vim /etc/systemd/system/`api`.service


```bash
[Unit]
Description=Run Django API
After=network.target

[Service]
Type=simple
WorkingDirectory=/usr/local/src/rspsrv
EnvironmentFile=/usr/local/src/rspsrv/rspsrv/settings/local.env
ExecStart=/usr/local/bin/pipenv run uwsgi --ini /opt/rspsrv/uwsgi/uwsgi.ini
StandardOutput=journal
StandardError=journal
Restart=on-failure

[Install]
WantedBy=multi-user.target
```