from rest_framework.permissions import BasePermission

from rspsrv.tools.permissions import Group


class IsSales(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name=Group.SALES).exists():
            return True
