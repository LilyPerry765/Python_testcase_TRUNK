from django.contrib import admin

from rspsrv.apps.siam.models import SuspendHistory


@admin.register(SuspendHistory)
class SuspendHistoryAdminModel(admin.ModelAdmin):
    search_fields = [
        'subscription_code',
        'number',
    ]

    list_display = (
        'id',
        'subscription_code',
        'number',
        'susp_id',
        'susp_type',
        'susp_order',
        'created_at',
    )
    list_filter = (
        'susp_id',
        'susp_type',
        'susp_order',
        'created_at',
    )
    ordering = ('-created_at',)

    readonly_fields = (
        'id',
        'subscription_code',
        'number',
        'susp_id',
        'susp_type',
        'susp_order',
        'created_at',
    )
    list_per_page = 20

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
