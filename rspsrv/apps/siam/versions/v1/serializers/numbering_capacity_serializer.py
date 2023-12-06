import calendar

import jdatetime
from rest_framework import serializers

from rspsrv.apps.siam.models import NumberingCapacity


class NumberingCapacitySerializer(serializers.ModelSerializer):
    odate = serializers.SerializerMethodField()

    class Meta:
        model = NumberingCapacity
        fields = [
            'id',
            'ASR1',
            'CER2',
            'ASR3',
            'POI4',
            'ASR5_land',
            'ASR5_cell',
            'ASR6',
            'CER7',
            'ABR8_land',
            'ABR8_cell',
            'ASR9_land',
            'ASR9_cell',
            'odate'
        ]

    def get_odate(self, obj):
        return str(
                jdatetime.datetime.fromgregorian(
                    date=obj.odate
                ).date()
            )
