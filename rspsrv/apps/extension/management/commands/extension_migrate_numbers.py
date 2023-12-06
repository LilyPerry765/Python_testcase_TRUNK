from django.core.management.base import BaseCommand

from rspsrv.apps.extension.models import Extension
from rspsrv.tools.utility import Helper


class Command(BaseCommand):
    help = 'Update Extension numbers based on conventions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--number',
            type=str,
            help='A number to update'
        )

    def handle(self, *args, **options):
        if options['number']:
            extensions = Extension.objects.filter(
                extension_number__number=options['number'],
                external_call_enable=True,
            )
        else:
            extensions = Extension.objects.filter(
                external_call_enable=True,
            )

        count = int(0)
        if extensions is not None:
            for extension in extensions:
                try:
                    number = Helper.normalize_number(
                        extension.extension_number.number,
                    )
                    callerid = Helper.normalize_number(
                        extension.callerid,
                    )

                    if number:
                        extension.extension_number.number = number
                        extension.extension_number.save()

                    if callerid:
                        extension.callerid = callerid
                        extension.save()

                    count += 1
                except Exception as e:
                    print(e)

        self.stdout.write(
            "{} extension numbers are updated in Extensions".format(count),
        )
