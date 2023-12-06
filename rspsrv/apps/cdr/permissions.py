from django.conf import settings
from rest_framework.permissions import BasePermission


class CDRPermission(BasePermission):
    """
    Allows access only to authenticated users for safe methods.
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            token = request.POST.get('token', None)

            return token == settings.APPS['fax']['post_received_fax_token']

