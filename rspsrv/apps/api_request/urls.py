from django.conf.urls import include
from django.urls import re_path

urlpatterns = [
    re_path(r'api/', include('rspsrv.apps.api_request.api_urls')),
    re_path(r'web/', include('rspsrv.apps.api_request.web_urls')),
]
