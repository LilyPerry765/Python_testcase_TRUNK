from rest_framework import serializers

from rspsrv.apps.siam.versions.v1.config import ForwardTypes


class ForwardSerializer(serializers.Serializer):
    def to_representation(self, queryset):
        result = {
            'id': queryset.id,
            'diverted_number': queryset.subscription.number,
            'acceptor_number': queryset.forward_to,
            'date': queryset.created_at,
            'type': ForwardTypes.ALL_CALLS_0,
        }

        return result
