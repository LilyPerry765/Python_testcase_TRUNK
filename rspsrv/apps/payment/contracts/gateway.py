from django.conf import settings


class GatewayContract:
    def __init__(self, user, app, related_name, gateway):
        pass

    @property
    def config(self):
        raise NotImplementedError

    @property
    def user(self):
        raise NotImplementedError

    @property
    def app(self):
        raise NotImplementedError

    @property
    def gateway(self):
        raise NotImplementedError

    def send(self, params):
        raise NotImplementedError

    def gateway_url(self, **kwargs):
        raise NotImplementedError

    def result_page_url(self, **kwargs):
        raise NotImplementedError

    def verify(self, params):
        raise NotImplementedError

    def get_url(self, uri):
        return '{base_url}/{uri}'.format(
            base_url=self.config['base_url'].strip("/"),
            uri=uri,
        )

    @staticmethod
    def get_post_back_url(
            gateway,
            app,
            related_name,
            payment_id,
            invoice_id
    ):
        url = '{base_url}/payment/web/verify?' \
              'sub_domain={sub_domain}&' \
              'gateway={gateway}&' \
              'app={app}&' \
              'related_name={related_name}&' \
              'payment_id={payment_id}&' \
              'redirect_to={redirect_to}'

        url = url.format(
            base_url=settings.RESPINA_BASE_ADDRESS_PAYMENT_PROXY,
            sub_domain=settings.RESPINA_SUB_DOMAIN,
            gateway=gateway,
            app=app,
            related_name=related_name,
            payment_id=payment_id,
            redirect_to=settings.APPS['payment']['redirect'][app].format(
                invoice_id=invoice_id,
            ),
        )

        return url
