from rest_framework.permissions import BasePermission

from rspsrv.tools.permissions import Group


class IsFinance(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name=Group.FINANCE).exists():
            return True
