from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from rangefilter.filter import DateRangeFilter

from rspsrv.apps.subscription.models import (
    Subscription,
    MaxCallConcurrencyHistory,
)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'customer_link',
        'operator_link',
        'subscription_type',
        'subscription_code',
        'allow_inbound',
        'allow_outbound',
        'activation',
        'is_allocated',
        'created_at',
    )
    list_filter = (
        'subscription_type',
        'is_allocated',
        'allow_inbound',
        'allow_outbound',
        'activation',
        ('created_at', DateRangeFilter),
    )
    search_fields = (
        'number',
        'subscription_code',
    )
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'subscription_type',
                'subscription_code',
                'number',
                'customer',
                'operator',
            ),
        }),
        ('Details', {
            'fields': (
                ('is_allocated', 'activation'),
                ('allow_inbound', 'allow_outbound', 'international_call',),
            ),
        }),
        ('Other Information', {
            'fields': (
                ('max_call_concurrency',),
                ('destination_type', 'destination_number',),
                ('destination_type_off', 'destination_number_off',),
                ('destination_type_in_list',),
                'destination_number_in_list',
                ('outbound_prefix', 'outbound_min_length',),
                ('latitude', 'longitude',),
                'ip',
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

    def operator_link(self, obj):
        link = " - "
        if obj.operator:
            url = reverse(
                "admin:membership_user_change",
                args=[obj.operator.id],
            )
            link = '<a href="{url}">{username}</a>'.format(
                url=url,
                username=obj.operator.username,
            )

        return mark_safe(link)

    operator_link.short_description = 'Operator'

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

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False


@admin.register(MaxCallConcurrencyHistory)
class MaxCallConcurrencyHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'subscription_link',
        'old_value',
        'new_value',
        'created_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )
    search_fields = (
        'subscription__number',
        'subscription__subscription_code',
    )
    readonly_fields = [
        'id',
        'old_value',
        'new_value',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'subscription_link',
            ),
        }),
        ('Details', {
            'fields': (
                'old_value',
                'new_value',
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

    def subscription_link(self, obj):
        link = " - "
        if obj.subscription:
            url = reverse(
                "admin:subscription_subscription_change",
                args=[obj.subscription.id],
            )
            link = '<a href="{url}">{number}</a>'.format(
                url=url,
                number=obj.subscription.number,
            )

        return mark_safe(link)

    subscription_link.short_description = 'Subscription'

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False
