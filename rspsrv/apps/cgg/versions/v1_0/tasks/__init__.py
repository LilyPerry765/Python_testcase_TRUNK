import logging

from celery import shared_task

from rspsrv.apps.membership.versions.v1.services.customer import (
    CustomerService,
)
from rspsrv.apps.mis.versions.v1_0.services.mis import MisService
from rspsrv.apps.subscription.versions.v1.services.subscription import (
    SubscriptionService,
)

logger = logging.getLogger("common")


@shared_task
def send_notification_to_mis(
        customer_id,
        email_subject,
        email_content,
        sms_content,
):
    customer_code = CustomerService.get_customer_code_from_id(
        customer_id=customer_id,
    )
    try:
        MisService.send_notification(
            customer_code=customer_code,
            email_subject=email_subject,
            email_content=email_content,
            sms_content=sms_content,
        )
    except Exception as e:
        logger.error("Exception: %s" % e)


@shared_task
def send_notification_to_mis_with_subscription(
        subscription_code,
        email_subject,
        email_content,
        sms_content,
):
    customer_code = SubscriptionService.get_customer_code_from_subscription(
        subscription_code=subscription_code,
    )
    try:
        MisService.send_notification(
            customer_code=customer_code,
            email_subject=email_subject,
            email_content=email_content,
            sms_content=sms_content,
        )
    except Exception as e:
        logger.error("Exception: %s" % e)
