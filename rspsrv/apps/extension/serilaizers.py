from rspsrv.tools.serializers import RespinaSerializer
from rspsrv.tools.utility import Helper


class ExtensionSerializer(RespinaSerializer):
    def get_dict(self):

        record = {
            'id': self.model.id,
            'customer_code': self.model.customer_code,
            'prime_code': self.model.prime_code,
            'callerid': self.model.callerid,
            'endpoint': self.model.endpoint.id if self.model.endpoint else None,
            'extension_number': self.model.extension_number.number,
            'created_at': Helper.get_timestamp(self.model.created_at),
            'password': self.model.password,
            'status': self.model.status,
            'web_enabled': self.model.web_enabled,
            'external_call_enable': self.model.external_call_enable,
            'record_all': self.model.record_all,
            'show_contacts': self.model.show_contacts,
            'ring_seconds': self.model.ring_seconds,
            'subscription': self.model.subscription.id if
            self.model.subscription else None,
            'subscription_number': self.model.subscription.number if
            self.model.subscription else None,
            'destination_type_off': self.model.destination_type_off,
            'destination_number_off': self.model.destination_number_off,
            'destination_type_no_answer':
                self.model.destination_type_no_answer,
            'destination_number_no_answer':
                self.model.destination_number_no_answer,
            'destination_type_in_list': self.model.destination_type_in_list,
            'destination_number_in_list':
                self.model.destination_number_in_list,
            'forward_to': self.model.forward_to,
            'call_waiting': self.model.call_waiting,
            'enabled': self.model.enabled,
            'international_call': self.model.international_call,
            'inbox_enabled': self.model.inbox_enabled
        }

        return record


class ExtensionNumberSerializer(RespinaSerializer):
    def get_dict(self):
        record = {
            'id': self.model.id,
            'number': self.model.number
        }
        return record


