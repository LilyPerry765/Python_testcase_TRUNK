import random
from datetime import timedelta, datetime

from django.core.management.base import BaseCommand
from django_seed import Seed

from rspsrv.apps.cdr.models import CDR


def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)


class Command(BaseCommand):
    help = 'Seed fake data into CDRs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=str,
            help='Number of faked CDRs'
        )

    def handle(self, *args, **options):
        c = 1000000
        if options['count']:
            try:
                c = int(float(options['count']))
            except ValueError:
                pass
        # CDR.objects.all().delete()
        seeder = Seed.seeder()
        seeder.add_entity(CDR, c, {
            'call_id_prefix': lambda obj: random.randint(0, c * 100),
            'call_id': lambda obj: random.randint(0, c * 100),
            'caller': lambda obj: "+98{}".format(
                random.randint(100000000, 1000000000),
            ),
            'called': lambda obj: "+98{}".format(
                random.randint(100000000, 1000000000),
            ),
            'direction': lambda obj: 'inbound' if random.randint(
                0,
                2,
            ) >= 1 else 'outbound',
            'source_ip': lambda obj: ".".join(
                map(str, (random.randint(0, 255) for _ in range(4)))),
            'destination_ip': lambda obj: ".".join(
                map(str, (random.randint(0, 255) for _ in range(4)))),
            'end_cause': lambda obj: random.randint(0, 40),
            'call_date': lambda obj: random_date(
                datetime.strptime('1/1/2019 01:00 AM', '%m/%d/%Y %I:%M %p'),
                datetime.strptime('9/28/2020 11:59 PM', '%m/%d/%Y %I:%M %p')
            ),
            'call_otime': lambda obj: random_date(
                datetime.strptime('1/1/2019 01:00 AM', '%m/%d/%Y %I:%M %p'),
                datetime.strptime('9/28/2020 11:59 PM', '%m/%d/%Y %I:%M %p')
            ).time(),
            'call_odate': lambda obj: random_date(
                datetime.strptime('1/1/2019 01:00 AM', '%m/%d/%Y %I:%M %p'),
                datetime.strptime('9/28/2020 11:59 PM', '%m/%d/%Y %I:%M %p')
            ),
        })

        seeder.execute()
        self.stdout.write(
            "{} new CDRs faked".format(c),
        )
