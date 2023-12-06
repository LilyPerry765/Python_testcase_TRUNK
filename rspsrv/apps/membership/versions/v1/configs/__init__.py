from django.utils.translation import gettext_lazy as _


class MFAConfig:
    class URLs:
        GENERATE = '/api/v1/tokens/generate/'
        VALIDATE = '/api/v1/tokens/validate/'


class MembershipConfiguration:
    USER_GENDER = (
        ('female', _('Female')),
        ('male', _('Male')),
    )
    USER_TYPES = (
        ('individual', _('Individual')),
        ('corporation', _('Corporation')),
    )

    class APILabels:
        LOGIN = "Login"
        GENERATE_TOKEN = "Generate token"
        CREATE_USER = "Create user"
        UPDATE_USER = "Update user"
        DELETE_USER = "Delete user"
        RESET_PASSWORD = "Reset password"
        SET_PASSWORD = "Set password"
        EMPOWER_USER = "Activate or deactivate user"
        RECOVER_PASSWORD_RESET = "Recover password reset"
        IMPERSONATE_USER = "Impersonate user"
        REVOKE_IMPERSONATE_USER = "Revoke impersonate user"
