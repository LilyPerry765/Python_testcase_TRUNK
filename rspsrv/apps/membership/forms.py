from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm


class AuthAdminForm(AdminAuthenticationForm):
    if not settings.DEBUG:
        captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox(
            attrs={
                'data-theme': 'light',
                'data-size': 'normal',
                'style': ('transform:scale(1.157);-webkit-transform:scale(1.157);'
                          'transform-origin:0 0;-webkit-transform-origin:0 0;')
            }
        ))
