from django.core.management.base import BaseCommand

from rspsrv.apps.cdr.models import CDR
from rspsrv.tools.utility import Helper


class Command(BaseCommand):
    help = 'Update CDRs caller and callee numbers based on conventions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--caller',
            type=str,
            help='A caller number to update'
        )
        parser.add_argument(
            '--callee',
            type=str,
            help='A callee number to update'
        )

    def handle(self, *args, **options):
        cdrs = None
        if options['callee'] or options['caller']:
            if options['caller']:
                cdrs = CDR.objects.filter(
                    caller=options['caller'],
                )
            if options['callee']:
                cdrs = CDR.objects.filter(
                    called=options['callee'],
                )
        else:
            cdrs = CDR.objects.all()

        count = int(0)
        if cdrs is not None:
            for cdr in cdrs:
                try:
                    caller = Helper.normalize_number(
                        cdr.caller,
                    )
                    if caller:
                        cdr.caller = caller
                    callee = Helper.normalize_number(
                        cdr.called,
                    )
                    if callee:
                        cdr.called = callee
                    cdr.save()
                    count += 1
                except Exception as e:
                    print(e)

        self.stdout.write(
            "{} caller and callee are updated in CDRs".format(count),
        )