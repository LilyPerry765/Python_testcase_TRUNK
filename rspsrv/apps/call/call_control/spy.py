import json

import requests
from django.conf import settings


class LIData(object):
    pass


class Interception(object):
    @staticmethod
    def check_for_spy(number):
        try:
            r = requests.post(
                url=settings.LI_GATE.HOST +
                    settings.LI_GATE.Requests.check_for_spying,
                data=json.dumps({"number": number[3:]})
            )
        except (requests.HTTPError, requests.ConnectionError):
            return False

        data = json.loads(r.text)
        if not len(data):
            return []

        batch = list()
        for d in data:
            l = LIData()
            for k in d:
                setattr(l, k, d[k])
            batch.append(l)

        return batch
