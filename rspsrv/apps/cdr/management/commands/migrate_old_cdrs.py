from django.core.management.base import BaseCommand

from rspsrv.apps.cdr.models import CDR
from rspsrv.apps.extension.models import Extension


class Command(BaseCommand):
    help = 'Migrate old CDRs data to new model.'

    def handle(self, *args, **options):
        all_cdrs = CDR.objects.all()
        for cdr in all_cdrs:
            if cdr.direction == 'internal':
                cdr.caller_extension = cdr.caller
                cdr.called_extension = cdr.called
                cdr.save()
                cdr.caller = None
                cdr.called = None
            elif cdr.direction == 'outbound':
                cdr.caller_extension = cdr.caller
                extension = Extension.objects.filter(extension_number__number=cdr.caller).first()
                cdr.save()
                cdr.caller = None
                if extension:
                    subscription_number = extension.subscription.number if \
                        extension.subscription else None
                    cdr.caller = subscription_number
            cdr.save()

        self.stdout.write(self.style.SUCCESS('Successfully migrated all CDRs data.'))
