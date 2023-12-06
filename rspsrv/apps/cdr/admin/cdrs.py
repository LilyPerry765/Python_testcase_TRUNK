import csv

from django.contrib import admin
from django.http import HttpResponse
from rangefilter.filter import DateRangeFilter

from rspsrv.apps.cdr.admin import filters
from rspsrv.apps.cdr.models import CDR


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(
                                                                        meta
                                                                        )
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response

    export_as_csv.short_description = "Export Selected"


@admin.register(CDR)
class CDRAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'call_date',
        'caller',
        'called',
        'talk_time',
        'duration',
        'cost',
        'direction',
        'end_cause',
        'state',
        'created_at'
    )
    list_per_page = 20

    def cost(self, obj):
        return obj.rate * obj.talk_time

    list_filter = (
        ('duration', filters.Duration),
        ('created_at', DateRangeFilter),
    )

    exclude = ('last_audited_cdr',)

    search_fields = (
        'caller_customer_id',
        'callee_customer_id',
        'caller_subscription_code',
        'callee_subscription_code',
        'caller',
        'called',
    )

    actions = ["export_as_csv"]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
