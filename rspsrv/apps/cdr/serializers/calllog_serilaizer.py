import calendar

from rest_framework import serializers

from rspsrv.apps.cdr.models import CDR


class CallLogSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = CDR
        fields = [
            'id',
            'caller',
            'called',
            'caller_extension',
            'called_extension',
            'talk_time',
            'direction',
            'caller_name',
            'called_name',
            'end_cause',
            'created_at',
        ]

    def get_created_at(self, obj):
        return int(calendar.timegm(obj.created_at.utctimetuple()))
