import datetime
import os

from khayyam import JalaliDate

from rspsrv.apps.invoice.versions.v1_0.config import InvoiceConfiguration
from rspsrv.apps.payment.versions.v1_0.config.config import (
    PaymentConfiguration,
)

PROJECT_ROOT_PATH = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def abs_path(relative_path):
    return os.path.join(PROJECT_ROOT_PATH, relative_path)


def get_bool(value=None):
    if not value:
        return False

    try:
        value = int(value)
    except ValueError:
        value = value.strip()
        return value.lower() == 'true'
    else:
        return value > 0


DEBUG = get_bool(os.getenv('RSPSRV_DEBUG', False))
SECRET_KEY = "(7!=bjdf@+78=roknro)g-wac_^o7_pb7h4_4rosd6ig1i2y5s"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'wkhtmltopdf',
    'rangefilter',
    'django_mysql',
    'rest_framework',
    'rspsrv',
    'rspsrv.apps.membership',
    'rspsrv.apps.call',
    'rspsrv.apps.endpoint',
    'rspsrv.apps.extension',
    'rspsrv.apps.subscription',
    'rspsrv.apps.cdr',
    'rspsrv.apps.payment',
    'rspsrv.apps.invoice',
    'rspsrv.apps.package',
    'rspsrv.apps.crm',
    'rspsrv.apps.siam',
    'rspsrv.apps.cgg',
    'rspsrv.apps.branch',
    'rspsrv.apps.interconnection',
    'rspsrv.apps.ocs',
    'rspsrv.apps.mis.apps.MisConfig',
    'rspsrv.apps.data_migration',
    'rspsrv.apps.file',
    'rspsrv.apps.api_request',

    # Health check apps
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    'captcha'
]

RECAPTCHA_PUBLIC_KEY = str(os.getenv('RECAPTCHA_PUBLIC_KEY'))
RECAPTCHA_PRIVATE_KEY = str(os.getenv('RECAPTCHA_PRIVATE_KEY'))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


class API_VERSIONS:
    V1 = 'v1'  # Version for Our CRM Panel.
    V2 = 'v2'

    @staticmethod
    def get_versions():
        return (
            API_VERSIONS.V1,
            API_VERSIONS.V2,
        )

    @staticmethod
    def get_latest():
        return API_VERSIONS.get_versions()[-1]


REST_FRAMEWORK = {
    'EXCEPTION_HANDLER':
        'rspsrv.tools.exception_handler.rspsrv_exception_handler',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rspsrv.tools.nexfon_backend.NexfonJSONWebTokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
    'DATETIME_FORMAT': '%s.%f',
    'DEFAULT_VERSION': API_VERSIONS.get_latest(),
    'ALLOWED_VERSIONS': API_VERSIONS.get_versions(),
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if not get_bool(os.getenv('RSPSRV_DEBUG')):
    MIDDLEWARE.append('pybrake.django.AirbrakeMiddleware')
AUTH_USER_MODEL = 'membership.User'
AUTHENTICATION_BACKENDS = (
    'rspsrv.tools.nexfon_backend.NexfonModelBackend',
)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.NumericPasswordValidator',
    },
    {
        'NAME': 'rspsrv.tools.validators.PasswordNumberValidator',
    },
    {
        'NAME': 'rspsrv.tools.validators.PasswordUpperOrLowercaseValidator',
    },
    {
        'NAME': 'rspsrv.tools.validators.PasswordSymbolValidator',
    },

]
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
IGNORE_CREATION_FLOW = get_bool(
    os.getenv('RSPSRV_IGNORE_CREATION_FLOW', False)
)
STATIC_URL = "/{}/".format(os.getenv('RSPSRV_STATIC_URL', "static").strip("/"))
STATIC_ROOT = os.getenv('RSPSRV_STATIC_ROOT', "static")
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)
MEDIA_URL = '/site_media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'site_media')
ROOT_URLCONF = 'rspsrv.urls'
LOG_PATH = os.path.join(BASE_DIR, 'logs')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %("
                      "message)s",
            'datefmt': "%Y/%m/%d %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'common': {
            'level': 'DEBUG',
            "filename": os.path.join(LOG_PATH, 'common.log'),
            'formatter': 'verbose',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'D',
            'interval': 1,
        },
        'backend': {
            'level': 'DEBUG',
            "filename": os.path.join(LOG_PATH, 'backend.log'),
            'formatter': 'verbose',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'D',
            'interval': 1,
        },
        'call': {
            'level': 'DEBUG',
            "filename": os.path.join(LOG_PATH, 'call.log'),
            'formatter': 'verbose',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'D',
            'interval': 1,
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['backend'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['backend'],
            'level': 'ERROR',
            'propagate': False,
        },
        'common': {
            'handlers': ['common', 'console'],
            'level': 'DEBUG',
        },
        'call': {
            'handlers': ['call', 'console'],
            'level': 'DEBUG',
        },
    },
}

CONTACT_DEFAULT_IMAGE = 'contacts_images/default.jpg'
USER_DEFAULT_IMAGE = 'user_image/default.jpg'

SIZE_UNIT = {
    'KB': 1 << 10,
    'MB': 1 << 20,
    'GB': 1 << 30,
    'TB': 1 << 40,
    'PB': 1 << 50,
}

ARI_PROCESS_UNIQUE_NAME = 'respina_ari'

FILE_UPLOAD_HANDLERS = (
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",)

CLIENT_DEFAULT_AVATAR = 'client/logo-default.svg'

MAX_CALL_LOG_COUNT = 100

COUNTRY_CODE = '98'
CITY_CODE = '21'

# WKHTMLTOPDF Variables.
if os.getenv('RSPSRV_WKHTMLTOPDF_CMD'):
    WKHTMLTOPDF_CMD = os.getenv('RSPSRV_WKHTMLTOPDF_CMD')
    WKHTMLTOPDF_CMD_OPTIONS = {
        # 'quiet': False,
        'margin-top': 2,
        'margin-left': 2,
        'margin-right': 2,
        'enable-local-file-access': True
    }

AIRBRAKE = dict(
    project_id=1,
    project_key='fa92145aad384fabbc2c3feecbae9e30',
    environment='production',
    host='https://ems.nexfon.ir'
)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%% Production.py
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
ALLOWED_HOSTS = ['*']

WEBSITE_DOMAIN = os.getenv('RSPSRV_RESPINA_BASE_ADDRESS')
WEBSITE_TITLE = 'Nexfon Fusion'
DEFAULT_EMAIL = 'y.khahani@respina.net'

MEMBERSHIP_EXPORT_USERSTAT_URI = 'http://127.0.0.1:8078/api/v1.0/user_status/'
MEMBERSHIP_EXPORT_GETUSERSTAT_URI = \
    'http://127.0.0.1:8078/api/v1.0/user_status/%s/'
SEND_EVENT_TO_TORIO_API_URL = 'http://http://127.0.0.1:8078/api/v1.0/event/'
TORIO_SECRET_KEY = '(7!=bjdf@+78=roknro)g-wac_^o7_pb7h4_4rosd6ig1i2y6p'
IMAGE_DEFAULT = 'user_image/default.png'

RSPSRV_REDIS = {
    'address': 'rspsrv-redis.nexfon-staging.svc',
    'port': 6379,
}

DASHBOARD_REDIRECT_ABSOLUTE = os.getenv('RSPSRV_DASHBOARD_REDIRECT_ABSOLUTE')
DASHBOARD_RESPINA_REDIRECT_ABSOLUTE = os.getenv(
    'RSPSRV_DASHBOARD_RESPINA_REDIRECT_ABSOLUTE'
)
PAYMENT_REDIRECT_RELATIVE = os.getenv('RSPSRV_PAYMENT_REDIRECT_RELATIVE')
RESET_PASSWORD_REDIRECT_RELATIVE = os.getenv(
    'RSPSRV_RESET_PASSWORD_REDIRECT_RELATIVE'
)
PAYMENT_REDIRECT = {
    InvoiceConfiguration.InvoiceTypes.INVOICE:
        '?invoice_id={invoice_id}',
    InvoiceConfiguration.InvoiceTypes.BASE_BALANCE_INVOICE:
        '?base_balance_invoice_id={invoice_id}',
    InvoiceConfiguration.InvoiceTypes.CREDIT_INVOICE:
        '?credit_invoice_id={invoice_id}',
    InvoiceConfiguration.InvoiceTypes.PACKAGE_INVOICE:
        '?package_invoice_id={invoice_id}',
}

PAYMENT_GATEWAYS = {
    'mis': {
        # Basic Auth for Username "respina" & Password "^&%0F23kj48ed@#$".
        'api_key': os.getenv('RSPSRV_PAYMENT_GATEWAYS_MIS_API_KEY'),
        'base_url': os.getenv('RSPSRV_PAYMENT_GATEWAYS_MIS_BASE_URL'),
        'uris': {
            'send': 'newpay',
            'payment': 'gateway/{internal_transaction_id}',
            'verify': 'verifypay/{mis_token_code}/',
        },
    },
    PaymentConfiguration.Gateway.CREDIT: {},
    PaymentConfiguration.Gateway.OFFLINE: {},
}

# @TODO: Remove this
BILLING = {
    'task': {
        'billing_cycle_interval': 1.0,
        'export_periodic_bill_interval': 1.0 * 60 * 60 * 24 *
                                         JalaliDate.today().daysinmonth,
        'pay_unpaid_bill_task_interval': 30.0,
    },
    'core': {
        'cache_proxy': {
            'host': 'rspsrv-redis.nexfon-staging.svc',
            'port': '6379',
            'db': 0,
            'channel': 'command_channel',
            'auditor_channel': 'auditor_channel'
        },
        'engine_process_name': 'rtnbe_proc',
        'auditor_process_name': 'rtnbe_proc',
        'engine': {
            'fetch_message_interval': 1.0,
            'billing_cycle_interval': 10.0,
            'decrease_balance_interval': 30.0,
            'check_ari_process_running': 10.0,
        }
    },
    'payment_dead_line_day': 30,
    'machine_identity_name': "ctr",
}

APPS = {
    'call':
        {
            'call_queue':
                {
                    'global_timeout': 1800,
                    'ringing_timeout': 45
                }
        },
    'extension':
        {
            'default_parent_extension_suffix': os.getenv(
                'RSPSRV_EXTENSION_DEFAULT_PARENT_EXTENSION_SUFFIX'),
        },
    'recorded_call':
        {
            'record_location': os.getenv('RSPSRV_RECORDED_CALL_LOCATION'),
        },
    'payment': {
        'redirect': {
            'invoice': PAYMENT_REDIRECT[
                InvoiceConfiguration.InvoiceTypes.INVOICE
            ],
            'base_balance_invoice': PAYMENT_REDIRECT[
                InvoiceConfiguration.InvoiceTypes.BASE_BALANCE_INVOICE
            ],
            'credit_invoice': PAYMENT_REDIRECT[
                InvoiceConfiguration.InvoiceTypes.CREDIT_INVOICE
            ],
            'package_invoice': PAYMENT_REDIRECT[
                InvoiceConfiguration.InvoiceTypes.PACKAGE_INVOICE
            ],
        },
        'gateways': {
            PaymentConfiguration.Gateway.CREDIT:
                PAYMENT_GATEWAYS[PaymentConfiguration.Gateway.CREDIT],
            PaymentConfiguration.Gateway.OFFLINE:
                PAYMENT_GATEWAYS[PaymentConfiguration.Gateway.OFFLINE],
            'mis': PAYMENT_GATEWAYS['mis'],
        }
    },
    'extension_inbox': {
        'personal_greeting_default': os.getenv(
            'RSPSRV_PERSONAL_INBOX_GREETING_DEFAULT_NAME'
        )
    },
    'cdr': {
        'max_xlsx_records_number': 10000
    }
}

DEFAULT_PLAYBACK = {
    'EXTENSION_NOT_EXISTS': 'unk_ext_default',
    'EXTENSION_NOT_AVAILABLE': 'ext_navailable',
    'EXTERNAL_ENDING_16': 'external-end-cause-17',
    'EXTERNAL_ENDING_17': 'external-end-cause-17',
    'EXTERNAL_ENDING_19': 'external-end-cause-17',
    'EXTERNAL_ENDING_20': 'external-end-cause-20',
    'EXTERNAL_ENDING_31': 'call_not_possible',
    'EXTERNAL_ENDING_50': 'external-end-cause-50',
    'INBOX_DEFAULT_GREETING': 'inbox_greeting_default',
    'AUTH_INBOX_GREETING': 'auth_inbox_greeting_default',
    'AUTH_INBOX_DENIAL': 'auth_inbox_denial_default',
    'INBOX_EMPTY': 'inbox_empty_default',
    'BEEP': 'beep',
    'CALL_NOT_POSSIBLE': 'call_not_possible',
    'OUTBOUND_DISABLED': 'outbound_disabled',
    'EXTENSION_STATUS': {
        'PRE_STATUS': 'ext_status_pre_status1',
        'MENU': 'ext_status_ivr_menu1',
        'STATUS_SAVE': 'ext_status_status_save1',
        'STATUS_NOT_SAVE': 'ext_status_status_not_save1',
        'BAD_COMMAND': 'ext_status_bad_command1',
        'ASK_TO_SAVE': 'ext_status_ask_to_save1',
        'AVAILABLE': 'ext_status_available1',
        'DND': 'ext_status_dnd1',
        'FORWARD': 'ext_status_forward1',
        'ASK_TO_SAVE_FORWARD': 'ext_status_ask_to_save_forward1',
        'CHANGE_STATUS_TO': 'ext_status_change_status_to1'
    },
    'Call_QUEUE_AGENTS': {
        'ENTER_PASSWORD': 'enter_password',
        'ENTER_QUEUE_EXTENSION_NUMBER': 'enter_queue_extension_number',
        'STATUS_CHANGED': 'status_changed',
        'THERE_IS_NO_QUEUE': 'there_is_no_queue',
        'UNAUTHORIZED': 'unauthorized',
        'YOU_ARE_ACTIVE': 'you_are_active',
        'YOU_ARE_INACTIVE': 'you_are_inactive',
        'YOU_ARE_NOT_AGENT': 'you_are_not_agent',
    },
    'QUEUE': {
        'IN_THE_QUEUE': 'in_the_queue',
        'YOU_ARE_NUMBER': 'you_are_number'
    },
    'CARDINALS_PATH': 'fa/cardinals/',
    'ORDINALS_PATH': 'fa/ordinals/',
    'MONTHS_PATH': 'fa/months',
    'MINUTE': 'fa/minute',
    'HOUR_': 'fa/hour_',
}

ENDPOINT_CONTEXT = ""
CONTROL_TECHNOLOGY = "SIP"

OPERATOR_IDENTIFIER = "Respina-PJSC"

HI2_INTERVAL = 600
HI2_SEND_TIMEOUT = 10

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': os.getenv('RSPSRV_DATABASES_DEFAULT_HOST'),
        'PORT': os.getenv('RSPSRV_DATABASES_DEFAULT_PORT'),
        'NAME': os.getenv('RSPSRV_DATABASES_DEFAULT_NAME'),
        'USER': os.getenv('RSPSRV_DATABASES_DEFAULT_USER'),
        'PASSWORD': os.getenv('RSPSRV_DATABASES_DEFAULT_PASSWORD'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    },
    'cdr_db': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': os.getenv('RSPSRV_DATABASES_CDR_HOST'),
        'PORT': os.getenv('RSPSRV_DATABASES_CDR_PORT'),
        'NAME': os.getenv('RSPSRV_DATABASES_CDR_NAME'),
        'USER': os.getenv('RSPSRV_DATABASES_CDR_USER'),
        'PASSWORD': os.getenv('RSPSRV_DATABASES_CDR_PASSWORD'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "{}:{}/{}".format(
            os.getenv('RSPSRV_CELERY_CACHE_REDIS_HOST'),
            os.getenv('RSPSRV_CELERY_CACHE_REDIS_PORT'),
            os.getenv('RSPSRV_REDIS_CACHE_DATABASE'),
        ),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": os.getenv('RSPSRV_REDIS_CACHE_PREFIX')
    }
}
DATABASE_ROUTERS = ['rspsrv.tools.cdr_db_router.CdrRouter']
DATABASE_APPS_MAPPING = {'cdr': 'cdr_db'}

# Celery configs
CELERY_BROKER_URL = "{}:{}/{}".format(
    os.getenv('RSPSRV_CELERY_CACHE_REDIS_HOST'),
    os.getenv('RSPSRV_CELERY_CACHE_REDIS_PORT'),
    os.getenv('RSPSRV_REDIS_CELERY_DATABASE'),
)
CELERY_RESULT_BACKEND = "{}:{}/{}".format(
    os.getenv('RSPSRV_CELERY_CACHE_REDIS_HOST'),
    os.getenv('RSPSRV_CELERY_CACHE_REDIS_PORT'),
    os.getenv('RSPSRV_REDIS_CELERY_DATABASE'),
)
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 18000}
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

ASTERISK_PLAYBACK_LOCATION = '/var/lib/asterisk/sounds/'
SYS_CONF = {
    'boarder_ip': 'sbc-host',
    'proxy_address': 'lb-host',
}

LI_ENABLED = get_bool(os.getenv('RSPSRV_LI_ENABLED'))


class LIGate(object):
    HOST = os.getenv('RSPSRV_LI_GATE_HOST')

    class Requests(object):
        check_for_spying = '/target/check/'
        ftp_mediator = '/iri/exchange/'


LI_GATE = LIGate

SWITCHMANAGER_APP_NAME = os.getenv('RSPSRV_SWITCHMANAGER_APP_NAME')
CALL_CONCURRENCY_MACHINE_NAME = os.getenv(
    'RSPSRV_CALL_CONCURRENCY_MACHINE_NAME'
)

SWITCH_ARI = [
    {
        'HOST': os.getenv('RSPSRV_SWITCH_ARI_HOST'),
        'USER': os.getenv('RSPSRV_SWITCH_ARI_USER'),
        'PASSWORD': os.getenv('RSPSRV_SWITCH_ARI_PASSWORD')
    },
]

RESPINA_BASE_ADDRESS = os.getenv('RSPSRV_RESPINA_BASE_ADDRESS')
RESPINA_BASE_ADDRESS_PAYMENT_PROXY = os.getenv(
    'RSPSRV_RESPINA_BASE_ADDRESS_PAYMENT_PROXY')
RESPINA_SUB_DOMAIN = os.getenv('RSPSRV_RESPINA_SUB_DOMAIN')
NEXFON_BASE_URL = os.getenv('RSPSRV_NEXFON_BASE_URL')
NEXFON_URIS = {
    'payment': {
        'create': 'internal/crm/payment/',
        'update': 'internal/crm/payment/{uid}',
        'delete': 'internal/crm/payment/{uid}',
    }
}

RSP_ASCII_NAME = 'Respina'

JWT_AUTH = {
    'JWT_ALLOW_REFRESH': True,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=1),
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=3),
    'JWT_RESPONSE_PAYLOAD_HANDLER':
        'rspsrv.tools.jwt_payload_handler.jwt_payload_handler',

}

CALL_ID_PREFIX = 1
Q_DEL_HISTORIES = os.getenv('RSPSRV_QUEUE_DELETE_OLD_HISTORIES')
LANGUAGES = (
    ('fa-IR', 'Farsi'),
    ('en-US', 'English'),
)
LANGUAGE_CODE = 'fa-IR'
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

SBC_MAC = os.getenv('RSPSRV_SBC_MAC')
SBC_PUBLIC_IP = os.getenv('RSPSRV_SBC_PUBLIC_IP')


class NSS:
    base_url = os.getenv('RSPSRV_NSSـBASE_URL')

    class URIs:
        cdr = 'cdr'


EXTERNAL_CALL_RINGING_TIMEOUT = os.getenv(
    'RSPSRV_EXTERNAL_CALL_RINGING_TIMEOUT'
)
BILLING_ENABLED = get_bool(os.getenv('RSPSRV_BILLING_ENABLED'))
ASTERISK_DB = {
    'host': os.getenv('RSPSRV_ASTERISK_DB_HOST'),
    'user': os.getenv('RSPSRV_ASTERISK_DB_USER'),
    'password': os.getenv('RSPSRV_ASTERISK_DB_PASSWORD'),
    'db': os.getenv('RSPSRV_ASTERISK_DB_DB'),
    'domain': os.getenv('RSPSRV_ASTERISK_DOMAIN'),
}
USER_RECOVER_PASSWORD_TOKEN_EXPIRE = datetime.timedelta(hours=24 * 30)


class TokenService:
    MAX_TOKEN_VALIDATION_ATTEMPTS = 5
    MAX_TRY_FOR_UNIQUENESS = 5
    TOKEN_SIZE = 6
    ALPHANUM = True
    SUFFIX = ''
    PREFIX = ''
    EXPIRATION_DELTA = datetime.timedelta(hours=24)


TOKEN_SERVICE = TokenService


class ProductTypes:
    PERSONAL = 'personal'
    ORGANIZATIONAL = 'organizational'
    SMALL_ORGANIZATIONAL = 'small_organizational'
    TRUNK = 'trunk'


PRODUCT_TYPES = ProductTypes
PRODUCT_TYPE = ProductTypes.TRUNK

SBC_DB = {
    'host': os.getenv('RSPSRV_SBC_DB_HOST'),
    'user': os.getenv('RSPSRV_SBC_DB_USER'),
    'password': os.getenv('RSPSRV_SBC_DB_PASSWORD'),
    'db': os.getenv('RSPSRV_SBC_DB_DB'),
}

DISPATCHER = {
    'url': os.getenv('RSPSRV_DISPATCHER_URL'),
    'destination': os.getenv('RSPSRV_DISPATCHER_DESTINATION'),
    'db': {
        'host': os.getenv('RSPSRV_DISPATCHER_URL_HOST'),
        'user': os.getenv('RSPSRV_DISPATCHER_URL_USER'),
        'password': os.getenv('RSPSRV_DISPATCHER_URL_PASSWORD'),
        'db': os.getenv('RSPSRV_DISPATCHER_URL_DB'),
    }
}

GLOBAL_REDIS = {
    'host': os.getenv('RSPSRV_GLOBAL_REDIS_HOST'),
    'port': os.getenv('RSPSRV_GLOBAL_REDIS_PORT'),
    'call_concurrency_db': os.getenv(
        'RSPSRV_REDIS_CALL_CONCURRENCY_DATABASE'
    ),
    'billing_db': os.getenv('RSPSRV_GLOBAL_REDIS_BILLING_DB'),
    'auditor_db': os.getenv('RSPSRV_GLOBAL_REDIS_AUDITOR_DB'),
}


class SiamApp:
    # All API Request(s) to Siam App which Included this Token in their Header
    # Are Allowed.
    API_TOKEN = os.getenv('RSPSRV_SIAMAPP_API_TOKEN')


SIAM_APP = SiamApp

NOTIFICATION_TEMPLATE_PATH = os.getenv(
    'RSPSRV_NOTIFICATION_TEMPLATE_PATH'
)


class MIS:
    class API:
        BASE_URL = os.getenv('RSPSRV_MIS_BASE_URL')
        KEY = os.getenv('RSPSRV_MIS_KEY')

    # Sorry, This is to the ridiculous API design of CRM
    DEFAULT_ACCOUNT_ID = os.getenv('RSPSRV_MIS_DEFAULT_ACCOUNT_ID')


EXTERNAL_CALL_TIMEOUT = os.getenv('RSPSRV_EXTERNAL_CALL_TIMEOUT_LENV')


class CGG:
    API_URL = os.getenv('RSPSRV_CGRATES_GATEWAY_API_URL')
    AUTH_TOKEN_OUT = os.getenv('RSPSRV_CGRATES_GATEWAY_AUTH_TOKEN_OUT')
    AUTH_TOKEN_IN = os.getenv('RSPSRV_CGRATES_GATEWAY_AUTH_TOKEN_IN')


CGG = CGG

FILE_SERVICE = {
    "api_url": os.getenv('RSPSRV_FILE_SERVICE_BASE_URL'),
    "auth_token": os.getenv('RSPSRV_FILE_SERVICE_AUTHORIZATION_HEADER')
}
MFA_SERVICE = {
    "api_url": os.getenv('RSPSRV_MFA_SERVICE_BASE_URL'),
    "auth_token": os.getenv('RSPSRV_MFA_SERVICE_AUTHORIZATION_HEADER'),
    "consumer_name": os.getenv('RSPSRV_MFA_SERVICE_CONSUMER_NAME'),
}
# Max duration of a call
MAX_CALL_DURATION_SECONDS = int(
    os.getenv('RSPSRV_MAX_CALL_DURATION_SECONDS', '3600'),
)
# Kazoo related settings
#KAZOO_KAMAILIO_DB = {
#    "host": os.getenv('RSPSRV_KAZOO_KAMAILIO_DB_HOST'),
#    "port": str(os.getenv('RSPSRV_KAZOO_KAMAILIO_DB_PORT')),
#    "name": os.getenv('RSPSRV_KAZOO_KAMAILIO_DB_NAME'),
#    "user": os.getenv('RSPSRV_KAZOO_KAMAILIO_DB_USER'),
#    "password": os.getenv('RSPSRV_KAZOO_KAMAILIO_DB_PASSWORD'),
#}
KAZOO_UAC_EXPIRES = os.getenv('RSPSRV_KAZOO_UAC_EXPIRES')
KAZOO_KAMAILIO_R_DOMAIN = os.getenv('RSPSRV_KAZOO_KAMAILIO_R_DOMAIN')
KAZOO_KAMAILIO_JSON_RPC_URL = os.getenv('RSPSRV_KAZOO_KAMAILIO_JSON_RPC_URL')
KAZOO_KAMAILIO_JSON_RPC_TOKEN = os.getenv(
    'RSPSRV_KAZOO_KAMAILIO_JSON_RPC_X_AUTH_TOKEN'
)
KAZOO_SBC = os.getenv('RSPSRV_KAZOO_SBC')


class CRMApp:
    DEFAULT_CUSTOMER_ADMIN_USERNAME = os.getenv(
        'RSPSRV_DEFAULT_CUSTOMER_ADMIN_USERNAME',
        'admin',
    )
    CACHE_EXPIRY = int(
        os.getenv('RSPSRV_CACHE_EXPIRY_CRM', 86400)
    )

    class Crm:
        AUTH_TOKEN = os.getenv('RSPSRV_CRM_AUTH_TOKEN')


CRM_APP = CRMApp


class DataMigrationApp:
    AUTH_TOKEN = os.getenv('RSPSRV_DATA_MIGRATION_AUTH_TOKEN')


class TIO:
    base_url = os.getenv('RSPSRV_TIO_BASE_URL')
    AUTH_TOKEN = os.getenv('RSPSRV_TIO_AUTH_TOKEN', "WdmnJAlNt03Vc8YuozF1RGotnbmDQhUkR3U4ZLpaoTdX9aS5rCo4Yb5GSkzsqqgi")

    class URIs:
        cdr = 'api/cdr/'
        csv = 'api/cdr/export/csv'


STORAGE_BARCODE_PATH = os.path.join(os.path.join(BASE_DIR, "static"), 'barcode')
os.makedirs(name=STORAGE_BARCODE_PATH, mode=0o777, exist_ok=True)
