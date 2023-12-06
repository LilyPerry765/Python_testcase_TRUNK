import logging
import uuid
from datetime import datetime, timedelta

import pymysql
import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger("common")


@shared_task
def will_reload_uac():
    KazooKamailioDatabase.reload_uac()


class KazooKamailioDatabase(object):
    sbc = settings.KAZOO_SBC
    domain = settings.KAZOO_KAMAILIO_R_DOMAIN
    expires = settings.KAZOO_UAC_EXPIRES

    @classmethod
    def connect(cls):
        connection = pymysql.connect(
            host=settings.KAZOO_KAMAILIO_DB['host'],
            port=settings.KAZOO_KAMAILIO_DB['port'],
            db=settings.KAZOO_KAMAILIO_DB['name'],
            user=settings.KAZOO_KAMAILIO_DB['user'],
            password=settings.KAZOO_KAMAILIO_DB['password'],
        )

        return connection, connection.cursor()

    @classmethod
    def reload_uac(cls, ):
        url = settings.KAZOO_KAMAILIO_JSON_RPC_URL
        token = settings.KAZOO_KAMAILIO_JSON_RPC_TOKEN
        try:
            res = requests.post(
                url,
                headers={
                    'Content-Type': 'application/json',
                    'x-auth-token': token,
                },
                json={
                    "jsonrpc": "2.0",
                    "method": "uac.reg_reload",
                    "id": uuid.uuid4().hex
                }
            )
            if not res.ok:
                logger.info("UAC Reg SBC Kamailio will be reloaded in 150s")
                apply_time = datetime.now() + timedelta(seconds=150)
                will_reload_uac.apply_async(
                    args=(),
                    eta=apply_time,
                )
                return
            logger.info("UAC Reg SBC Kamailio is successfully reloaded")
        except Exception:
            raise

    @classmethod
    def unregister(cls, extension_number, reload=True):
        cursor = None
        conn = None
        try:
            conn, cursor = cls.connect()
            cursor.execute("DELETE FROM uacreg WHERE l_uuid='{}';".format(
                extension_number,
            )
            )
            conn.commit()
        finally:
            if reload:
                cls.reload_uac()
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @classmethod
    def register(cls, extension_number, password, prime_code, reload=True):
        cursor = None
        conn = None
        try:
            conn, cursor = cls.connect()
            cursor.execute(
                "SELECT l_uuid FROM uacreg WHERE l_uuid='{}';".format(
                    extension_number,
                )
            )
            exist = len(cursor.fetchall()) > 0
            if exist:
                query = "UPDATE uacreg set auth_password='{}' where " \
                        "l_uuid='{}';".format(
                    password,
                    extension_number,
                )
            else:
                query = "INSERT INTO uacreg(l_uuid, l_username, l_domain, " \
                        "r_username, r_domain, realm, auth_username, " \
                        "auth_password, auth_ha1, auth_proxy, expires, " \
                        "flags, reg_delay) VALUES ('{}','{}','{}','{}','{}'," \
                        "'{}','{}','{}','{}','{}','{}','{}','{}');".format(
                    extension_number,
                    extension_number,
                    f"pro-{int((str(prime_code).split('prime-')[1]))}",
                    extension_number,
                    cls.domain,
                    cls.domain,
                    extension_number,
                    password,
                    "",
                    cls.sbc,
                    cls.expires,
                    0,
                    0,
                )
            try:
                cursor.execute(query)
                conn.commit()
            except pymysql.IntegrityError as e:
                logger.error(
                    "IntegrityError, Duplicate entry: %s, query: %s".format(
                        e,
                        query,
                    )
                )
        finally:
            if reload:
                cls.reload_uac()
            if cursor:
                cursor.close()
            if conn:
                conn.close()
