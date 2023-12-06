import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordNumberValidator(object):
    def validate(self, password, user=None):
        if not re.findall('\d', password):
            raise ValidationError(
                _("The password must contain at least 1 digit, 0-9."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 digit, 0-9."
        )


class PasswordUpperOrLowercaseValidator(object):
    def validate(self, password, user=None):
        if not re.findall('[a-zA-Z]', password):
            raise ValidationError(
                _("The password must contain at least 1 uppercase or lower letter, A-Z."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 uppercase or lower letter, A-Z."
        )


class PasswordSymbolValidator(object):
    def validate(self, password, user=None):
        if not re.findall('[!#$%&@]', password):
            raise ValidationError(
                _("The password must contain at least 1 special character: " +
                  "!#$%&@"),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 special character: " +
            "!#$%&@"
        )
