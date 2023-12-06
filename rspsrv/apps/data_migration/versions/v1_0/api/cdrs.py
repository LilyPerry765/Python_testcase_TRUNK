import json
import logging

from rspsrv.apps.data_migration.versions.v1_0.api.base import (
    BaseDataMigrationAPIView,
)
from rspsrv.apps.data_migration.versions.v1_0.services import ImportCdr
from rspsrv.tools import response
from rspsrv.tools.response import response

logger = logging.getLogger("common")


class CdrAPIView(BaseDataMigrationAPIView):
    def post(self, request):
        cdrs = json.loads(request.data)
        try:
            ImportCdr.import_cdrs(cdrs)
        except Exception as e:
            return response(
                request,
                status=500,
                error=e,
            )

        return response(
            request,
            status=200,
            message='CDRs migrated successfully',
        )



