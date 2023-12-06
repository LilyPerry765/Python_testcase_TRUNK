## Updating RSPSRV

```
python manage.py compilemessages
python manage.py makemigrations
python manage.py migrate --database=default
python manage.py migrate --database=cdr_db
```