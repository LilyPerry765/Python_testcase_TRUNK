import os
from zipfile import ZipFile

from celery import shared_task
from django.conf import settings

from rspsrv.tools.utility import Helper


@shared_task
def create_bill_zip_file(file_names):
    zip_name = 'bill_zip_'+Helper.generate_guid()
    zip_directory = settings.APPS['bill']['zip_bill_location']
    zip_path = os.path.join(zip_directory, '_'+zip_name)
    if not os.path.isdir(zip_directory):
        os.mkdir(zip_directory)
    with ZipFile(zip_path, 'w') as zip_file:
        for file in file_names:
            if not os.path.isfile(file):
                continue
            file_name = file.split('/')[-1]
            zip_file.write(file, file_name)

    done_zip_path = os.path.join(zip_directory, zip_name + '.zip')
    os.rename(zip_path, done_zip_path)

    return done_zip_path
