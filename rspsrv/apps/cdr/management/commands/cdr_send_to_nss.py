from django.core.management.base import BaseCommand

from rspsrv.apps.cdr.services.services import CDRSendToNSS


class Command(BaseCommand):
    help = 'Send CDRs to NSS which Created in Some Days ago.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Send CDRs from How many Days ago to Send them to NSS.',
        )

    def handle(self, *args, **options):
        CDRSendToNSS.send(options['days'])
