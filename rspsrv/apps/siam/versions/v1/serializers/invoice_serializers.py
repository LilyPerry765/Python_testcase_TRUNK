import jdatetime
from rest_framework import serializers

from rspsrv.tools.utility import Helper


class InvoicesResponseSerializer(serializers.BaseSerializer):
    def to_representation(self, bill_obj):
        return {
            'id': bill_obj['id'],
            'invoice_id': bill_obj['tracking_code'],
            'number': bill_obj['number'],
            'subscription_code': bill_obj['subscription_code'],
            'number_type': 'permanent',
            'invoice_type': bill_obj['invoice_type_code'],
            'period': bill_obj['period_count'],
            'status_code': bill_obj['status_code'],
            'amount': bill_obj['total_cost'],
            'subscription_cost': bill_obj['subscription_fee'],
            'debt': bill_obj['debt'],
            'discount': bill_obj['discount'],
            'tax_cost': bill_obj['tax_cost'],
            'tax_percent': bill_obj['tax_percent'],
            'payment_id': bill_obj['credit_invoice_id'],
            'payment_datetime': str(
                jdatetime.datetime.fromtimestamp(
                    int(float(bill_obj['paid_at'])),
                ) if bill_obj['paid_at'] else ''
            ),
            'from_datetime': str(
                jdatetime.datetime.fromtimestamp(
                    int(float(bill_obj['from_date'])),
                )
            ),
            'to_datetime': str(
                jdatetime.datetime.fromtimestamp(
                    int(float(bill_obj['to_date'])),
                )
            ),
            'domestic_cost': int(
                float(bill_obj['landlines_local_cost'])) + int(
                float(bill_obj['landlines_long_distance_cost'])) + int(
                float(bill_obj['mobile_cost'])) + int(
                float(bill_obj['landlines_corporate_cost'])) + int(
                float(bill_obj['landlines_local_cost_prepaid'])) + int(
                float(bill_obj['landlines_long_distance_cost_prepaid'])) + int(
                float(bill_obj['mobile_cost_prepaid'])) + int(
                float(bill_obj['landlines_corporate_cost_prepaid'])),
            'domestic_duration': Helper.convert_nano_seconds_to_seconds(
                float(bill_obj['landlines_local_usage']) + float(
                    bill_obj['landlines_long_distance_usage']) + float(
                    bill_obj['mobile_usage']) + float(
                    bill_obj['landlines_corporate_usage']) + float(
                    bill_obj['landlines_local_usage_prepaid']) + float(
                    bill_obj['landlines_long_distance_usage_prepaid']) + float(
                    bill_obj['mobile_usage_prepaid']) + float(
                    bill_obj['landlines_corporate_usage_prepaid']),
            ),
            'international_cost': int(float(bill_obj['international_cost'])),
            'international_duration': Helper.convert_nano_seconds_to_seconds(
                float(bill_obj['international_usage']),
            ),
            'total_landlines_cost': int(float(
                bill_obj['landlines_local_cost_prepaid'])) + int(float(
                bill_obj['landlines_long_distance_cost_prepaid'])) + int(float(
                bill_obj['landlines_local_cost'])) + int(float(
                bill_obj['landlines_long_distance_cost'])),
            'total_landlines_duration': Helper.convert_nano_seconds_to_seconds(
                float(bill_obj['landlines_local_usage_prepaid']) + float(
                    bill_obj['landlines_long_distance_usage_prepaid']) + float(
                    bill_obj['landlines_local_usage']) + float(
                    bill_obj['landlines_long_distance_usage']),
            ),
            'total_cellphone_cost': int(float(bill_obj['mobile_cost'])) + int(
                float(bill_obj['mobile_cost_prepaid'])),
            'total_cellphone_duration': Helper.convert_nano_seconds_to_seconds(
                float(bill_obj['mobile_usage']) + float(
                    bill_obj['mobile_usage_prepaid'])
            ),
            'total_corporate_cost': int(float(
                bill_obj['landlines_corporate_cost'])) + int(float(
                bill_obj['landlines_corporate_cost_prepaid'])),
            'total_corporate_duration': Helper.convert_nano_seconds_to_seconds(
                float(bill_obj['landlines_corporate_usage']) + float(
                    bill_obj['landlines_corporate_usage_prepaid']),
            ),
        }

    def to_internal_value(self, data):
        pass

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
