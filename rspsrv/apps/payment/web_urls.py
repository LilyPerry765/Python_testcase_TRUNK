from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r'^verify$',
        views.VerifyView.as_view(),
        name='verify_get_post',
    ),
]
