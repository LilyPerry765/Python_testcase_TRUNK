import django.views.static
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import re_path
from django.utils.translation import gettext as _
from rest_framework_jwt.views import refresh_jwt_token

from rspsrv.apps.membership.forms import AuthAdminForm

# Chge admin site login form
admin.autodiscover()
admin.site.login_form = AuthAdminForm
admin.site.login_template = 'admin/login.html'

urlpatterns = [
    re_path(r'^health-check/', include('health_check.urls')),
    re_path(r'^site_media/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),

    re_path(r'^api/token-refresh/', refresh_jwt_token),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^membership/', include(('rspsrv.apps.membership.urls','rspsrv.apps.membership'), namespace='membership')),
    re_path(r'^endpoint/', include(('rspsrv.apps.endpoint.urls', 'rspsrv.apps.endpoint'), namespace='endpoint')),
    re_path(r'^extension/', include(('rspsrv.apps.extension.urls', 'rspsrv.apps.extension'), namespace='extension')),
    re_path(r'^subscription/', include(('rspsrv.apps.subscription.urls', 'rspsrv.apps.subscription'), namespace='subscription')),
    re_path(r'^cdr/', include(('rspsrv.apps.cdr.urls', 'rspsrv.apps.cdr'), namespace='cdr')),
    re_path(r'^payment/', include(('rspsrv.apps.payment.urls', 'rspsrv.apps.payment'), namespace='payment')),
    re_path(r'^crm/', include(('rspsrv.apps.crm.urls', 'rspsrv.apps.crm'), namespace='crm')),
    re_path(r'^siam/', include(('rspsrv.apps.siam.urls', 'rspsrv.apps.siam'), namespace='siam')),
    re_path(r'^ocs/', include(('rspsrv.apps.ocs.urls', 'rspsrv.apps.ocs'), namespace='ocs')),
    re_path(r'^branch/', include(('rspsrv.apps.branch.urls', 'rspsrv.apps.branch'), namespace='branch')),
    re_path(r'^interconnection/', include(('rspsrv.apps.interconnection.urls', 'rspsrv.apps.interconnection'), namespace='interconnection')),
    re_path(r'^package/', include(('rspsrv.apps.package.urls', 'rspsrv.apps.package'), namespace='package')),
    re_path(r'^invoice/', include(('rspsrv.apps.invoice.urls', 'rspsrv.apps.invoice'),namespace='invoice')),
    re_path(r'^data-migration/', include(('rspsrv.apps.data_migration.urls', 'rspsrv.apps.data_migration'),namespace='data_migration')),
    re_path(r'^file/', include(('rspsrv.apps.file.urls', 'rspsrv.apps.file'), namespace='file')),
]

# Change admin site title
admin.site.index_title = _('Nexfon')
admin.site.site_header = _('Nexfon Administration')
admin.site.site_title = _('Nexfon Administration')
