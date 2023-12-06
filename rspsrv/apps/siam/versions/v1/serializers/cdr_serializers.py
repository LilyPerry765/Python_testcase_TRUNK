import jdatetime
from django.conf import settings
from rest_framework import serializers


class CallType:
    VOICE = 'voice'
    URBAN = 'urban'
    INTERCITY = 'intercity'
    INTERNATIONAL = 'international'


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Request Serializers %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Response Serializers %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class CDRsResponseSerializer(serializers.BaseSerializer):
    def to_representation(self, cdr_obj):
        result = {
            'date_time': str(
                jdatetime.datetime.fromgregorian(
                    date=cdr_obj.created_at
                )
            ),
            'origin': cdr_obj.caller,
            'destination': cdr_obj.called,
            'call_type': CallType.VOICE,
            'call_time': cdr_obj.talk_time,
            'cost': cdr_obj.talk_time * cdr_obj.rate,
            'discount': 0,  # FIXME: Where Is Discount Data in Our Service?!
            'sip_url': 'sip:{number}@{domain}.nexfon.ir'.format(
                number=self.context.get('number'),
                domain=settings.RESPINA_SUB_DOMAIN,
            ),
            'lat': self.context.get('lat'),
            'long': self.context.get('long'),
        }

        return result

    def to_internal_value(self, data):
        pass

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
