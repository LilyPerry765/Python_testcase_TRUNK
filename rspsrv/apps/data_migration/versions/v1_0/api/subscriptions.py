import json
import logging

from rspsrv.apps.data_migration.versions.v1_0.api.base import (
    BaseDataMigrationAPIView,
)
from rspsrv.apps.data_migration.versions.v1_0.services import (
    ImportSubscription,
)
from rspsrv.tools import response
from rspsrv.tools.response import response

logger = logging.getLogger("common")


class SubscriptionAPIView(BaseDataMigrationAPIView):
    def post(self, request):
        subscriptions = json.loads(request.data)
        try:
            ImportSubscription.import_subscriptions(subscriptions)
        except Exception as e:
            return response(
                request,
                status=500,
                error=e,
            )

        return response(
            request,
            status=200,
            message="Subscriptions data migrated",
        )



