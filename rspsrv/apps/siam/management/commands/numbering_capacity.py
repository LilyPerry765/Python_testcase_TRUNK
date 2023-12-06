from datetime import date

from django.core.management import BaseCommand

from rspsrv.apps.siam.models import NumberingCapacity
from rspsrv.apps.siam.versions.v1.services.numbering_capacity_service import NumberingCapacityService


class Command(BaseCommand):
    help = "Generate numbering capacities"

    def add_arguments(self, parser):
        parser.add_argument(
            '--peak',
            type=int,
            default=0,
            help='Defines start peak hour (For example: 11)'
        )
        parser.add_argument(
            '--date',
            type=str,
            default='0',
            help='Defines the date to be performed (For example: 2021-01-01)'
        )

    def handle(self, *args, **options):
        peak = options['peak'] if options['peak'] != 0 else 11
        filter_date = options['date'] if options['date'] != '0' else date.today()

        asr1 = NumberingCapacityService.get_asr1(filter_date, peak)
        cer2 = NumberingCapacityService.get_cer2(filter_date, peak)
        asr3 = NumberingCapacityService.get_asr3(filter_date, peak)
        poi4 = NumberingCapacityService.get_poi4(filter_date, peak)
        asr5_land = NumberingCapacityService.get_asr5_land(filter_date, peak)
        asr5_cell = NumberingCapacityService.get_asr5_cell(filter_date, peak)
        asr6 = 0
        cer7 = 0
        abr8_land = NumberingCapacityService.get_abr8_land(filter_date, peak)
        abr8_cell = NumberingCapacityService.get_abr8_cell(filter_date, peak)
        asr9_land = NumberingCapacityService.get_asr9_land(filter_date, peak)
        asr9_cell = NumberingCapacityService.get_asr9_cell(filter_date, peak)

        repeat_data = NumberingCapacity.objects.filter(odate=filter_date).exists()
        if repeat_data:
            print("It has already been inserted")
        else:
            NumberingCapacity.objects.create(
                ASR1=asr1, CER2=cer2, ASR3=asr3, POI4=poi4, ASR5_land=asr5_land, ASR5_cell=asr5_cell,
                ASR6=asr6, CER7=cer7, ABR8_land=abr8_land, ABR8_cell=abr8_cell, ASR9_land=asr9_land,
                ASR9_cell=asr9_cell, odate=filter_date
            )
            print("Numbering capacities successfully inserted")
