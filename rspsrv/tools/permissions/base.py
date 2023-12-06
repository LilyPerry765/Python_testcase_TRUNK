from django.db.models import Q
from rest_framework.permissions import BasePermission, SAFE_METHODS


class Group:
    SUPPORT_ADMIN = 'support-admin'
    SUPPORT_OPERATOR = 'support-operator'
    CUSTOMER_ADMIN = 'customer-admin'
    CUSTOMER_OPERATOR = 'customer-operator'
    FINANCE = 'finance'
    SALES = 'sales'
    PHONE_OPERATOR = 'phone-operator'


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsReadyOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class CheckPermission:
    @staticmethod
    def is_customer(request):
        return request.user.groups.filter(
            Q(name=Group.CUSTOMER_ADMIN) |
            Q(name=Group.CUSTOMER_OPERATOR)
        ).exists()

    @staticmethod
    def is_support(request):
        return request.user.groups.filter(
            Q(name=Group.SUPPORT_ADMIN) |
            Q(name=Group.SUPPORT_OPERATOR)
        ).exists()

    @staticmethod
    def is_superuser(request):
        return request.user.is_superuser

    @classmethod
    def is_sales(cls, request):
        return request.user.groups.filter(
            name=Group.SALES
        ).exists()

    @classmethod
    def is_phone_operator(cls, request):
        return request.user.groups.filter(
            name=Group.PHONE_OPERATOR
        ).exists()
