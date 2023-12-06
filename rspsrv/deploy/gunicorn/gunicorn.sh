#!/bin/bash
set -e

NAME="RSPSRV Gunicorn"
RSPSRV_ENV_NAME="rspsrvenv"
RSPSRV_PATH=/home/torkashvand/www/rspsrv/
DJANGO_WSGI_MODULE=rspsrv.wsgi

echo "Starting $NAME as `whoami`"

cd $RSPSRV_PATH

#gunicorn -c /home/torkashvand/www/rspsrv/configs/gunicorn/gunicorn.conf.py rspsrv.wsgi
exec gunicorn -c $RSPSRV_PATH/configs/gunicorn/gunicorn.conf.py ${DJANGO_WSGI_MODULE}