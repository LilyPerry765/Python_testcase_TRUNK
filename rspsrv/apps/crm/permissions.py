from django.conf import settings
from rest_framework import permissions


class APICRMPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.META.get(
                'HTTP_AUTHORIZATION'
        ) == settings.CRM_APP.Crm.AUTH_TOKEN:
            return True

        return False
