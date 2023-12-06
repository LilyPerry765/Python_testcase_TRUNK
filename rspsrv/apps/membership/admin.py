from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from rangefilter.filter import DateRangeFilter

from rspsrv.apps.membership.models import (
    User,
    Customer,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['customer_code', 'id']
    list_display = (
        'id',
        'customer_code',
        'is_active',
        'deleted',
        'created_at',
        'updated_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )
    list_per_page = 20
    readonly_fields = [
        'id',
        'users',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'customer_code',
                'users',
                'is_active',
                'deleted',
            ),
        }),
        ('Dates', {
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )

    def users(self, obj):
        link = ""
        for user in obj.users.all():
            url = reverse(
                "admin:membership_user_change",
                args=[user.id],
            )
            link += '<a href="{url}">{username}</a>'.format(
                url=url,
                username=user.username,
            )

        return mark_safe(link)

    users.short_description = 'Users'

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'prime_code',
                'customer_link',
                'email',
                'mobile',
                'gender',
                'first_name',
                'last_name',
                'ascii_name',
                'job_title',
                'address',
                'birthday',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'deleted',
                'groups',
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'created_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2')
        }
         ),
    )
    list_display = (
        'id',
        'customer_link',
        'prime_code',
        'username',
        'mobile',
        'email',
        'is_superuser',
        'is_active',
        'created_at',
    )
    search_fields = (
        'customer__customer_code',
        'customer__id',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    readonly_fields = (
        'guid',
        'created_at',
        'customer_link',
        'username',
        'customer',
        'email',
        'mobile',
        'updated_at',
        'deleted',
        'is_active',
        'last_login',
        'prime_code',
    )
    list_filter = (
        'is_superuser',
        'is_active',
        'groups',
        'user_type',
        'gender',
    )
    ordering = ('-created_at',)

    def prime_code(self, obj):
        if obj.customer:
            return obj.customer.prime_code

        return " - "

    prime_code.short_description = 'Prime code'

    def customer_link(self, obj):
        link = " - "
        if obj.customer:
            url = reverse(
                "admin:membership_customer_change",
                args=[obj.customer.id],
            )
            link = '<a href="{url}">{customer_code}</a>'.format(
                url=url,
                customer_code=obj.customer.customer_code,
            )

        return mark_safe(link)

    customer_link.short_description = 'Customer'

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser


admin.site.register(User, CustomUserAdmin)
