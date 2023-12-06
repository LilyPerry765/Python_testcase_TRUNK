from calendar import timegm
from datetime import datetime

from django.conf import settings

from rspsrv.tools.utility import Helper


def jwt_payload_handler(token, user=None, request=None, impersonate=False):
    orig_user = None
    if impersonate is True:
        orig_user = request.user.id
    return {
        'token': Helper.jwt_encode(
            {
                'prime_code':
                    user.customer.id if user.customer else None,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'mobile': user.mobile,
                'groups': list(user.groups.all().values_list(
                    'name',
                    flat=True
                )),
                'impersonate': impersonate,
                'orig_user':orig_user,
                'exp': datetime.utcnow() + settings.JWT_AUTH[
                    'JWT_EXPIRATION_DELTA'],
                'orig_iat': timegm(
                    datetime.utcnow().utctimetuple()
                )
            }
        )
    }
