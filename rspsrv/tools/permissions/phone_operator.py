from rest_framework.permissions import BasePermission

from rspsrv.tools.permissions import Group


class IsPhoneOperatorPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name=Group.PHONE_OPERATOR).exists():
            return True
