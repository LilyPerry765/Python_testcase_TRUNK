from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from rspsrv.apps.extension.models import (
    Extension,
    ExtensionNumber,
)


@admin.register(Extension)
class ExtensionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer_link',
        'callerid',
        'extension_number',
        'status',
        'subscription',
    )
    readonly_fields = [
        'extension_number',
        'subscription',
        'created_at',
        'updated_at',
    ]
    list_filter = (
        'status',
    )
    fieldsets = (
        ('Base Information', {
            'fields': (
                'callerid',
                'password',
                'customer',
                'subscription',
                'extension_number',
                'endpoint',
                'status',
                'forward_to',
            ),
        }),
        ('Details', {
            'fields': (
                ('enabled', 'has_pro', 'international_call',),
                ('web_enabled', 'external_call_enable', 'inbox_enabled',),
                ('record_all', 'call_waiting', 'show_contacts',),
            ),
        }),
        ('Other Information', {
            'fields': (
                ('ring_seconds',),
                ('destination_type_off', 'destination_number_off',),
                (
                    'destination_type_no_answer',
                    'destination_number_no_answer',
                ),
                ('destination_type_in_list',),
                'destination_number_in_list',

            ),
        }),
        ('Dates', {
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    list_per_page = 20

    def customer_link(self, obj):
        link = " - "
        if obj.customer:
            url = reverse(
                "admin:membership_customer_change",
                args=[obj.customer.id],
            )
            link = '<a href="{url}">{prime_code}</a>'.format(
                url=url,
                prime_code=obj.customer.prime_code,
            )

        return mark_safe(link)

    customer_link.short_description = 'Prime code'

    search_fields = [
        'extension_number__number'
    ]

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False


@admin.register(ExtensionNumber)
class ExtensionNumberAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'type',
    )
    readonly_fields = [
        'number',
    ]
    list_filter = [
        'type',
    ]

    list_per_page = 20

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False
