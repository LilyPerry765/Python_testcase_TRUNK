import json
import logging

from rspsrv.apps.data_migration.versions.v1_0.api.base import (
    BaseDataMigrationAPIView,
)
from rspsrv.apps.data_migration.versions.v1_0.services import ImportInvoice
from rspsrv.tools import response
from rspsrv.tools.response import response

logger = logging.getLogger("common")


class InvoiceAPIView(BaseDataMigrationAPIView):
    def post(self, request):
        invoices = json.loads(request.data)
        try:
            ImportInvoice.import_invoices(invoices)
        except Exception as e:
            return response(
                request,
                error=e,
                status=500
            )

        return response(
            request,
            status=200,
            message="Invoices data migrated",
        )
