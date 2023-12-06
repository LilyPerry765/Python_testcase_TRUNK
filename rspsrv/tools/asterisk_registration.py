import logging

import pymysql
import pymysql.cursors
from django.conf import settings

from rspsrv.apps.subscription.utils import get_pure_number

logger = logging.getLogger(__name__)


class AsteriskDatabase(object):
    domain = settings.ASTERISK_DB['domain']

    @staticmethod
    def get_connection():
        connection = pymysql.connect(host=settings.ASTERISK_DB['host'],
                                     user=settings.ASTERISK_DB['user'],
                                     password=settings.ASTERISK_DB['password'],
                                     db=settings.ASTERISK_DB['db'])

        return connection, connection.cursor()

    @staticmethod
    def unregister(extension, password):
        cursor = None
        connection = None

        try:
            query = ("DELETE FROM sipusers WHERE name = '%s' " % extension)

            connection, cursor = AsteriskDatabase.get_connection()

            cursor.execute(query)

            cursor.execute("DELETE FROM sipregs WHERE name = '%s'" % extension)

            connection.commit()
        finally:
            if cursor:
                cursor.close()

            if connection:
                connection.close()

    @staticmethod
    def register(extension, password):
        cursor = None
        connection = None

        try:
            query = "SELECT ID FROM sipusers WHERE name= %s" % extension

            connection, cursor = AsteriskDatabase.get_connection()

            cursor.execute(query=query)
            exist = cursor.rowcount > 0
            if exist:
                query = ("UPDATE sipusers "
                         "SET name = '{name}', "
                         "defaultuser='{defaultuser}', "
                         "host='{host}' , "
                         "sippasswd='{sippasswd}' , "
                         "fromdomain='{fromdomain}' , "
                         "mailbox='{mailbox}' WHERE name = '{name}' ".format(name=extension,
                                                                             defaultuser=extension,
                                                                             host="dynamic",
                                                                             sippasswd=password,
                                                                             fromdomain=AsteriskDatabase.domain,
                                                                             mailbox=extension))
            else:
                query = ("INSERT INTO sipusers (name, "
                         "defaultuser, "
                         "host, "
                         "sippasswd, "
                         "fromdomain, "
                         "mailbox) VALUES ('{name}',"
                         "'{defaultuser}',"
                         "'{host}',"
                         "'{sippasswd}',"
                         "'{fromdomain}',"
                         "'{mailbox}')".format(name=extension,
                                               defaultuser=extension,
                                               host="dynamic",
                                               sippasswd=password,
                                               fromdomain=AsteriskDatabase.domain,
                                               mailbox=extension))

            try:
                cursor.execute(query)
                connection.commit()

                if not exist:
                    cursor.execute("INSERT INTO sipregs(name) VALUES('%s')" % extension)
                    connection.commit()

            except pymysql.IntegrityError as e:
                logger.error("IntegrityError, Duplicate entry: %s, query: %s" % (e, query))

        finally:
            if cursor:
                cursor.close()

            if connection:
                connection.close()

    @staticmethod
    def get_user_ip(number):
        pure_number = get_pure_number(number)
        query = None

        connection, cursor = AsteriskDatabase.get_connection()

        query = "SELECT username, received FROM location WHERE username={username} LIMIT 1".format(
            username=pure_number,
        )

        if query:
            cursor.execute(query)
            row = cursor.fetchall()

            if len(row):
                return (row[0][1]).split(':')[1]

        return None
