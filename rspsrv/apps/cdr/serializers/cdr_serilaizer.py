import calendar

from django.urls import reverse
from rest_framework import serializers

from rspsrv.apps.cdr.models import CDR
from rspsrv.tools.utility import Helper


class CDRSerializer(serializers.ModelSerializer):
    call_date = serializers.SerializerMethodField(source='call_date')
    recorded_audio = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    audio_link = serializers.SerializerMethodField()

    class Meta:
        model = CDR
        fields = (
            'id',
            'call_id_prefix',
            'call_id',
            'call_odate',
            'call_otime',
            'call_date',
            'caller',
            'called',
            'caller_extension',
            'called_extension',
            'parent_extension_number',
            'caller_trunk',
            'called_trunk',
            'duration',
            'talk_time',
            'call_type',
            'call_state',
            'action',
            'action_value',
            'direction',
            'source_ip',
            'destination_ip',
            'caller_name',
            'called_name',
            'device_serial_number',
            'reserved1',
            'reserved2',
            'end_cause',
            'state',
            'recorded_audio',
            'created_at',
            'updated_at',
            'audio_link',
        )

    def get_call_date(self, obj):
        return int(calendar.timegm(obj.call_date.utctimetuple()))

    def get_recorded_audio(self, obj):
        return obj.recorded_audio.name if obj.recorded_audio else None

    def get_created_at(self, obj):
        return int(calendar.timegm(obj.created_at.utctimetuple()))

    def get_updated_at(self, obj):
        return int(calendar.timegm(obj.updated_at.utctimetuple()))

    def get_audio_link(self, obj):
        payload = {'id': obj.id}
        token = Helper.jwt_encode(payload=payload)

        return reverse(
            'cdr:recorded_audio_download_signed', args=[
                obj.id,
                token
            ]
        )
