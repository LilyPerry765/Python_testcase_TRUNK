from rest_framework.permissions import BasePermission

from rspsrv.tools.permissions import Group


class IsCustomerOperator(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name=Group.CUSTOMER_OPERATOR).exists():
            return True


class IsCustomerAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.groups.filter(name=Group.CUSTOMER_ADMIN).exists():
            return True
