import json

from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from rangefilter.filter import DateRangeFilter

from rspsrv.apps.api_request.models import APIRequest


@admin.register(APIRequest)
class APIRequestAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = [
        'app_name',
        'label',
        'ip',
        'uri',
        'user__username',
        'user__mobile',
        'user__email',
        'request',
        'response',
    ]
    list_display = (
        'label',
        'user_link',
        'direction',
        'app_name',
        'http_method',
        'uri',
        'status_code',
        'ip',
        'created_at',
    )
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'app_name',
                'label',
                'uri',
                'user_link',

            ),
        }),
        ('Request & Response', {
            'fields': (
                'ip',
                'http_method',
                'direction',
                'status_code',
                'request_formatted',
                'response_formatted',
            ),
        }),
        ('Dates', {
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    list_filter = (
        'direction',
        'status_code',
        'http_method',
        ('created_at', DateRangeFilter),
    )
    ordering = ('-created_at',)
    list_per_page = 20

    def user_link(self, obj):
        link = " - "
        if obj.user:
            url = reverse(
                "admin:membership_user_change",
                args=[obj.user.id],
            )
            link = '<a href="{url}">{prime_code} {username}</a>'.format(
                url=url,
                username=obj.user.username,
                prime_code=obj.user.customer.prime_code if obj.user.customer
                else ''
            )

        return mark_safe(link)

    user_link.short_description = 'User'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def response_formatted(self, obj):
        return json.dumps(
            obj.response,
            ensure_ascii=False,
        )

    response_formatted.short_description = 'Response'

    def request_formatted(self, obj):
        return json.dumps(
            obj.request,
            ensure_ascii=False,
        )

    request_formatted.short_description = 'Request'
