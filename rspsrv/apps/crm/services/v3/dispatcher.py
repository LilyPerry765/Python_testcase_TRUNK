import logging

import pymysql
import pymysql.cursors
import requests
from django.conf import settings

from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class DispatcherService:
    @staticmethod
    def _connect():
        connection = pymysql.connect(
            host=settings.DISPATCHER['db']['host'],
            user=settings.DISPATCHER['db']['user'],
            password=settings.DISPATCHER['db']['password'],
            db=settings.DISPATCHER['db']['db'],
        )

        return connection, connection.cursor()

    @staticmethod
    def new_dispatch(set_id, flags=0, priority=0):
        """
        Insert a new dispatch into Kamailio's dispatcher table
        :param set_id:
        :type set_id:
        :param flags:
        :type flags:
        :param priority:
        :type priority:
        :return:
        :rtype:
        """
        destination = settings.DISPATCHER['destination']
        cursor = None
        connection = None
        set_id = Helper.set_id_from_number(
            number=set_id,
        )
        query = "INSERT INTO dispatcher (setid,destination,flags,priority) " \
                "VALUES ('{set_id}', '{destination}', 0, 0)".format(
            set_id=set_id,
            destination=destination,
            flags=flags,
            priority=priority
        )

        try:
            connection, cursor = DispatcherService._connect()
            cursor.execute(query=query)
            connection.commit()
        except Exception as e:
            logger.error(e)
            raise e
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
            # Reload DataBase for Dispatcher.
            try:
                requests.post(
                    settings.DISPATCHER['url'],
                    json={
                        "jsonrpc": "2.0",
                        "method": "dispatcher.reload",
                        "id": 1
                    }
                )
            except Exception:
                raise

    @staticmethod
    def remove_dispatch(set_id):
        """
        Remove an existing dispatch from Kamailio's dispatcher table
        :param set_id:
        :type set_id:
        :return:
        :rtype:
        """
        cursor = None
        connection = None
        set_id = Helper.set_id_from_number(
            number=set_id,
        )
        query = f"DELETE FROM dispatcher WHERE setid='{set_id}'"

        try:
            connection, cursor = DispatcherService._connect()
            cursor.execute(query=query)
            connection.commit()
        except Exception as e:
            logger.error(e)
            raise e
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
