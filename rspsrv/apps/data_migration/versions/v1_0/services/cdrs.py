import logging

from rspsrv.apps.call.call_control.channel import ChannelContext
from rspsrv.apps.cdr import models
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class ImportCdr:
    @classmethod
    def import_cdrs(cls, cdrs):
        for cdr in cdrs:
            cdr['called'] = Helper.normalize_number(cdr['called'])
            cdr['caller'] = Helper.normalize_number(cdr['caller'])
            if cdr['direction'] == ChannelContext.INBOUND:
                try:
                    subscription_obj = Subscription.objects.get(
                        number=cdr['called']
                    )
                    cdr['callee_subscription_code'] = \
                        subscription_obj.subscription_code
                    cdr['callee_customer_id'] = subscription_obj.customer.id
                except Subscription.DoesNotExist:
                    pass

            if cdr['direction'] == ChannelContext.OUTBOUND:
                try:
                    subscription_obj = Subscription.objects.get(
                        number=cdr['caller']
                    )
                    cdr['caller_subscription_code'] = \
                        subscription_obj.subscription_code
                    cdr['caller_customer_id'] = subscription_obj.customer.id
                except Subscription.DoesNotExist:
                    pass

            del cdr['id']
            try:
                cdr_obj = models.CDR.objects.create(**cdr)
                models.CDR.objects.filter(id=cdr_obj.id).update(
                    updated_at=cdr['updated_at'],
                    created_at=cdr['created_at']
                )
            except Exception as e:
                raise e
        return
