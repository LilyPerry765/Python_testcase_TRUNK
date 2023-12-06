import logging

from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import exceptions

from rspsrv.apps.call.apps.base import CallApplicationType
from rspsrv.apps.extension.models import Extension, ExtensionStatus
from rspsrv.apps.siam.models import SuspendHistory
from rspsrv.apps.siam.versions.v1 import serializers
from rspsrv.apps.siam.versions.v1.config import (
    ResponsesCode,
    ExceptionsCode,
    ForwardTypes,
    TransactionID,
)
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")


class TrunkService:
    @staticmethod
    @transaction.atomic
    def product_suspend(number, params):
        request_serializer = serializers.SuspendRequestSerializer(
            data=params,
        )

        try:
            request_serializer.is_valid(raise_exception=True)
        except exceptions.APIException:
            raise

        validated_data = request_serializer.validated_data

        try:
            subscription_obj = Subscription.objects.get(
                number=number
            )
        except Subscription.DoesNotExist as e:
            raise exceptions.NotFound(detail=e)
        except Subscription.MultipleObjectsReturned as e:
            raise api_exceptions.Conflict409(detail=e)

        activation = True if validated_data['susp_id'] == 1 else 0

        subscription_obj.activation = activation
        subscription_obj.save()

        if subscription_obj.operator:
            subscription_obj.operator.is_active = activation
            subscription_obj.operator.save()

        # Store suspend history
        suspend_history_obj = SuspendHistory()
        suspend_history_obj.subscription_code = \
            subscription_obj.subscription_code
        suspend_history_obj.number = subscription_obj.number
        suspend_history_obj.susp_id = validated_data['susp_id']
        suspend_history_obj.susp_type = validated_data['susp_type']
        suspend_history_obj.susp_order = validated_data['susp_order']
        suspend_history_obj.save()

        return validated_data

    @classmethod
    def get_forward_settings(cls, forwarder, acceptor):

        lookup = dict()
        query = None

        if forwarder and acceptor:
            lookup.update(
                forward_to=acceptor,
                extension_number__number=forwarder,
            )
            query = Extension.objects.filter(**lookup)
            if not query:
                raise api_exceptions.NotFound404()

        elif forwarder:
            lookup.update(
                extension_number__number=forwarder,
            )
            query = Extension.objects.filter(**lookup)

            if not query:
                e = api_exceptions.NotFound404(
                    detail=_('siam.msg.no.this.number.not.forwarded')
                )
                e.hint = (ResponsesCode.
                          ApplyForwardSettings.
                          IS_NOT_FORWARDED_RIGHT_NOW_3
                          )
                raise e

        elif acceptor:
            lookup.update(
                forward_to=acceptor,
            )
            query = Extension.objects.filter(**lookup)

            if not query:
                e = api_exceptions.NotFound404(
                    detail=
                    _('siam.msg.no.number.forwarded.to.this.number')
                )
                e.hint = (ResponsesCode.
                          ApplyForwardSettings.
                          NO_NUMBERS_FORWARDED_TO_THIS_NUMBER_6
                          )

                raise e

        if query:
            serializer = serializers.ForwardSerializer(query, many=True)

            return serializer.data
        else:
            raise api_exceptions.NotFound404()

    @classmethod
    def set_forward_settings(
            cls,
            forwarded_number,
            acceptor_number,
            action,
            forward_type,
    ):
        lookup = dict()

        if forwarded_number:
            lookup.update(
                extension_number__number=forwarded_number,
            )
        elif acceptor_number:
            lookup.update(
                forward_to=acceptor_number,
            )
        else:
            e = api_exceptions.ValidationError400(
                detail=_('siam.msg.invalid.number')
            )
            e.hint = ExceptionsCode.INVALID_NUMBER_5
            raise e

        query = Extension.objects.filter(**lookup)

        if query.exclude(subscription__activation=True):
            e = api_exceptions.Conflict409(
                detail=_('siam.msg.forwarding.this.number.impossible')
            )
            e.hint = ResponsesCode.ApplyForwardSettings\
                .FORWARD_THIS_NUMBER_IS_NOT_POSSIBLE_4
            raise e

        if forward_type == ForwardTypes.ALL_CALLS_0:
            if action == TransactionID.REMOVE_FORWARD_1:
                query.update(forward_to=None,
                             status=ExtensionStatus.AVAILABLE.Value,
                             )
            else:
                if query.exclude(forward_to=None):
                    e = api_exceptions.Conflict409(
                        detail=_('siam.msg.already.forwarded')
                    )
                    e.hint = \
                        ResponsesCode.ApplyForwardSettings.ALREADY_FORWARDED_TO_ANOTHER_NUMBER_2
                    raise e

                query.update(forward_to=acceptor_number,
                             status=ExtensionStatus.FORWARD.Value,
                             )

            return ResponsesCode.ApplyForwardSettings.SUCCESS_0

        if forward_type == ForwardTypes.NO_ANSWER_CALLS_1:
            if action == TransactionID.REMOVE_FORWARD_1:
                query.update(
                    destination_type_no_answer=CallApplicationType.end,
                    destination_number_no_answer=None,
                )

            else:

                if query.exclude(destination_number_no_answer=None):
                    e = api_exceptions.Conflict409(
                        detail=_('siam.msg.already.forwarded')
                    )
                    e.hint = \
                        ResponsesCode.ApplyForwardSettings.ALREADY_FORWARDED_TO_ANOTHER_NUMBER_2

                    raise e

                query.update(
                    destination_type_no_answer=CallApplicationType.EXTENSION,
                    destination_number_no_answer=acceptor_number,
                )

            return ResponsesCode.ApplyForwardSettings.SUCCESS_0

        if (
                forward_type == ForwardTypes.CALLEE_BUSY_2 or
                forward_type == ForwardTypes.CALLEE_NOT_AVAILABLE_3
        ):
            return ResponsesCode.ApplyForwardSettings.SUCCESS_0
