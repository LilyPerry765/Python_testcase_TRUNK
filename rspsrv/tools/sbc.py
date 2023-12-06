import logging

import pymysql
import pymysql.cursors
from django.conf import settings

logger = logging.getLogger(__name__)


class SBC(object):
    @staticmethod
    def get_connection():
        connection = pymysql.connect(
            host=settings.SBC_DB['host'],
            user=settings.SBC_DB['user'],
            password=settings.SBC_DB['password'],
            db=settings.SBC_DB['db']
        )

        return connection, connection.cursor()

    @staticmethod
    def get_user_ip(number):
        connection, cursor = SBC.get_connection()
        query = "SELECT username, received FROM location WHERE username='{username}' LIMIT 1".format(
            username=number,
        )
        cursor.execute(query)
        row = cursor.fetchall()

        if len(row):
            return (row[0][1]).split(':')[1]

        return None
