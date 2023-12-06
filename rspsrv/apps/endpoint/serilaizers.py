from rspsrv.tools.serializers import RespinaSerializer
from rspsrv.tools.utility import Helper


class BrandSerializer(RespinaSerializer):
    def get_dict(self):
        record = {
            'id': self.model.id,
            'name': self.model.name,
            'extra_options': self.model.extra_options,
            'created_at': Helper.get_timestamp(self.model.created_at),
            'updated_at': Helper.get_timestamp(self.model.updated_at),
        }

        return record


class EndpointSerializer(RespinaSerializer):
    def get_dict(self):
        subscription = {
            'id': None,
            'number': None,
        }
        if self.model.subscription:
            subscription = {
                'id': self.model.subscription.id,
                'number': self.model.subscription.number,
            }

        record = {
            'id': self.model.id,
            'brand': {
                'id': self.model.brand.id,
                'name': self.model.brand.name
            } if self.model.brand else None,
            'subscription': subscription,
            'mac_address': self.model.mac_address,
            'extra_options': self.model.extra_options,
            'enabled': self.model.enabled,
            'status': self.model.status,
            'ip_address': self.model.ip_address,
            'created_at': Helper.get_timestamp(self.model.created_at),
            'updated_at': Helper.get_timestamp(self.model.updated_at),
        }

        return record
