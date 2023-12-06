from django.conf import settings
from rest_framework import permissions


class ApiTokenPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.META.get(
                'HTTP_AUTHORIZATION'
        ) == settings.SIAM_APP.API_TOKEN:
            return True

        return False
