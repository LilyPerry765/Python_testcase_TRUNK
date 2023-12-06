import json
import logging

from rspsrv.apps.data_migration.versions.v1_0.api.base import (
    BaseDataMigrationAPIView,
)
from rspsrv.apps.data_migration.versions.v1_0.services import ImportExtensions
from rspsrv.tools import response
from rspsrv.tools.response import response

logger = logging.getLogger("common")


class ExtensionNumbersAPIViews(BaseDataMigrationAPIView):
    def post(self, request):
        numbers = json.loads(request.data)
        try:
            ImportExtensions.import_extension_numbers(numbers)
        except Exception as e:
            return response(
                request,
                status=500,
                error=e,
            )

        return response(
            request,
            status=200,
            message='Extension extension numbers migrated successfully',
        )


class ExtensionsAPIViews(BaseDataMigrationAPIView):
    def post(self, request):
        extensions = json.loads(request.data)
        try:
            ImportExtensions.import_extensions(extensions)
        except Exception as e:
            return response(
                request,
                status=500,
                error=e,
            )

        return response(
            request,
            status=200,
            message='Extensions migrated successfully',
        )
