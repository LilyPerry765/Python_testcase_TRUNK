from django.conf.urls import include
from django.urls import re_path

urlpatterns = [
    re_path(r'api/', include('rspsrv.apps.membership.api_urls')),
]