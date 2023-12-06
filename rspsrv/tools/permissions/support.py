from django.db.models import Q
from rest_framework.permissions import BasePermission

from rspsrv.tools.permissions import Group


class IsSupport(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(
                Q(name=Group.SUPPORT_ADMIN) |
                Q(name=Group.SUPPORT_OPERATOR)
        ).exists():
            return True
