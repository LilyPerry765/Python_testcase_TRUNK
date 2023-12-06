# --------------------------------------------------------------------------
# This service should not be responsible for ACL related tasks
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - package.py
# Created at 2020-6-15,  14:53:13
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import logging

from rspsrv.apps.cgg.versions.v1_0.services.cgg_service import CggService
from rspsrv.apps.package.versions.v1_0.config import PackageConfiguration

logger = logging.getLogger("common")


class PackageService:

    @classmethod
    def create_new_package(
            cls,
            payload=None
    ):
        relative_uri = PackageConfiguration.URLs.PACKAGES
        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            body=payload,
            http_method='post',
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def update_package(
            cls,
            package_id,
            payload=None,
    ):
        relative_uri = PackageConfiguration.URLs.PACKAGE
        relative_uri = relative_uri.format(
            pid=package_id,
        )
        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            body=payload,
            http_method='patch',
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def delete_package(
            cls,
            package_id,
    ):
        relative_uri = PackageConfiguration.URLs.PACKAGE
        relative_uri = relative_uri.format(
            pid=package_id,
        )
        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            http_method='delete',
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def get_package(
            cls,
            package_id
    ):
        relative_uri = PackageConfiguration.URLs.PACKAGE
        relative_uri = relative_uri.format(
            pid=package_id,
        )
        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            http_method='get',
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def get_packages(
            cls,
            query_params=None,
    ):
        relative_uri = PackageConfiguration.URLs.PACKAGES
        url = CggService.cgg_url(relative_uri, query_params)
        response = CggService.cgg_response(
            url,
            http_method='get',
            response_type=CggService.ResponseType.SINGLE if
            'bypass_pagination' in query_params else
            CggService.ResponseType.LIST,
        )

        return response
