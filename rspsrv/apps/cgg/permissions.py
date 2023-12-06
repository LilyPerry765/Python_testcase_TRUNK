from django.conf import settings
from rest_framework import permissions


class APICGRateSInPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.META.get(
                'HTTP_AUTHORIZATION',
        ) == settings.CGG.AUTH_TOKEN_IN:
            return True

        return False
