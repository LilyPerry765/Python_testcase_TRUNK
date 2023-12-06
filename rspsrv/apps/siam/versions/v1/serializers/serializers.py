from django.utils.translation import gettext as _
from rest_framework import serializers

choices_susp_id = (
    (0, _('siam.suspend')),
    (1, _('siam.release')),
)

choices_susp_type = (
    (2, _('siam.suspend_type.bidirectional')),
)

choices_susp_order = (
    ('3940000', _('siam.suspend_order.release')),
)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Request Serializers %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class SuspendRequestSerializer(serializers.Serializer):
    susp_id = serializers.ChoiceField(required=True, choices=choices_susp_id)
    susp_type = serializers.ChoiceField(
        required=True,
        choices=choices_susp_type,
    )
    susp_order = serializers.ChoiceField(
        required=True,
        choices=choices_susp_order,
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Response Serializers %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
