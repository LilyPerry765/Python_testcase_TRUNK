import json
import logging

from rspsrv.apps.data_migration.versions.v1_0.api.base import (
    BaseDataMigrationAPIView,
)
from rspsrv.apps.data_migration.versions.v1_0.services.notify import (
    MigrateNotify,
)
from rspsrv.tools import response
from rspsrv.tools.response import response

logger = logging.getLogger("common")


class NotifyAPIView(BaseDataMigrationAPIView):
    def post(self, request):
        body = json.loads(request.data)
        number = body['number']
        prime_only = body['prime_only']
        try:
            MigrateNotify.notify_migration(number, prime_only)
        except Exception as e:
            return response(
                request,
                error=e,
                status=500
            )

        return response(
            request,
            status=200,
            message="Notified",
        )
