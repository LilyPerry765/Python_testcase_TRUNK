from django.core.management.base import BaseCommand

from rspsrv.apps.mis.versions.v1_0.config import load_templates


class Command(BaseCommand):
    help = 'Load email templates from setting.NOTIFICATION_TEMPLATE_PATH'

    def handle(self, *args, **options):
        try:
            load_templates()
            self.stdout.write(
                "Templates loaded successfully"
            )
        except Exception as e:
            self.stdout.write(
                "Failed: {}".format(e)
            )
