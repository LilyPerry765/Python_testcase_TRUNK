from rest_framework.views import APIView

from rspsrv.apps.data_migration.permissions import DataMigrationPermission


class BaseDataMigrationAPIView(APIView):
    permission_classes = (DataMigrationPermission,)
