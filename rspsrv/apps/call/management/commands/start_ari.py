import glob
import os
import threading
import time

import redis
from django.conf import settings
from django.core.management.base import BaseCommand
from setproctitle import setproctitle

from rspsrv.apps.call.call_control.base import ARIManager, ARIDefaultManager
from rspsrv.apps.call.call_control.call_control import CallControl
from rspsrv.apps.cdr.models import CDR
from rspsrv.apps.subscription.models import Subscription


class PidFile(object):
    rename_pid_file_interval = \
        settings.BILLING['core']['engine']['check_ari_process_running']

    @staticmethod
    def rename_pid_file():
        pid_file = glob.glob('/tmp/respina_ari_*.pid')[-1]
        now = time.time()
        new_pid_file = "/tmp/respina_ari_{}.pid".format(now)
        os.rename(pid_file, new_pid_file)

        threading.Timer(PidFile.rename_pid_file_interval,
                        PidFile.rename_pid_file).start()

    @staticmethod
    def write_pid_file():
        pid = str(os.getpid())
        now = time.time()
        pid_file = "/tmp/respina_ari_{}.pid".format(now)

        if glob.glob('/tmp/respina_ari_*.pid'):
            pid_file = glob.glob('/tmp/respina_ari_*.pid')[-1]

        if os.path.isfile(pid_file):
            open(pid_file, 'w').write(pid)
            PidFile.rename_pid_file()
            return

        open(pid_file, 'w').write(pid)
        threading.Timer(PidFile.rename_pid_file_interval,
                        PidFile.rename_pid_file).start()


def remove_previous_ongoing_calls():
    global_redis = settings.GLOBAL_REDIS
    pool = redis.StrictRedis(
        host=global_redis['host'],
        port=global_redis['port'],
        db=global_redis['call_concurrency_db'],
    )
    for subscription in Subscription.objects.all():
        subscription_string = 'concurrency::{}::{}'.format(
            settings.CALL_CONCURRENCY_MACHINE_NAME,
            subscription.number
        )
        pool.delete(subscription_string)


class Command(BaseCommand):
    help = 'Runs ARI worker'

    def handle(self, *args, **options):
        try:
            ARIManager.st()
            ARIManager.init_billing_cache_proxy()
            ARIDefaultManager.client.on_channel_event(
                'StasisStart',
                CallControl.io_channel_callback,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR('ARI Service Failed to Start'))
            self.stdout.write(self.style.ERROR(e))
            raise

        cdrs = CDR.objects.filter(state='open',
                                  call_id_prefix=settings.CALL_ID_PREFIX)
        cdrs.update(state='closed')
        remove_previous_ongoing_calls()

        self.stdout.write(self.style.SUCCESS('Successfully started'))

        print('Process title: %s' % settings.ARI_PROCESS_UNIQUE_NAME)
        setproctitle(settings.ARI_PROCESS_UNIQUE_NAME)

        PidFile.write_pid_file()

        return
