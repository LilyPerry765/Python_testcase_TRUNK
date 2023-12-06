from rest_framework import permissions

from rspsrv.settings import base


class DataMigrationPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.META.get(
                'HTTP_AUTHORIZATION'
        ) == base.DataMigrationApp.AUTH_TOKEN:
            return True

        return False
