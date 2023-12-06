import requests
from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import status

from rspsrv.apps.file.versions.v1_0.config import FileConfigs
from rspsrv.apps.file.versions.v1_0.serializers import (
    UploadFileForm,
    UploadFileSerializer,
)
from rspsrv.tools import api_exceptions


def raise_exceptions(res):
    if res.status_code == status.HTTP_400_BAD_REQUEST:
        raise api_exceptions.ValidationError400(
            res.json()['error']
        )
    elif res.status_code == status.HTTP_404_NOT_FOUND:
        raise api_exceptions.NotFound404(
            res.json()['error']
        )
    elif res.status_code == status.HTTP_403_FORBIDDEN:
        raise api_exceptions.PermissionDenied403(
            res.json()['error']
        )
    elif res.status_code == status.HTTP_400_BAD_REQUEST:
        raise api_exceptions.Conflict409(
            res.json()['error']
        )
    else:
        raise api_exceptions.APIException(
            res.json()['error']
        )


class FileService:

    @classmethod
    def check_file_existence(cls, file_id):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': settings.FILE_SERVICE['auth_token']
        }
        try:
            base_url = settings.FILE_SERVICE['api_url'].strip("/")
            relative_url = FileConfigs.FILE_URL.strip("/").format(
                file_id=file_id,
            )
            url = "{}/{}/".format(
                base_url,
                relative_url,
            )
            res = requests.get(
                url=url,
                headers=headers,
                timeout=5.0,
            )
            if res.ok:
                return True
            return False
        except Exception:
            return False

    @classmethod
    def upload_file(cls, request, mime_types=None):
        if mime_types is None:
            mime_types = []
        files = []
        mimes = []
        for mime_type in mime_types:
            mimes.append(('mimeType', mime_type))
        form_file = UploadFileForm(request.POST, request.FILES)
        if not form_file.is_valid():
            raise api_exceptions.ValidationError400({
                'file': _('not a valid request')
            })
        else:
            for f in request.FILES.getlist('file'):
                tmp_name = f.file.name
                files.append(
                    ('file', (f.name, open(tmp_name, 'rb'), f.content_type)),
                )
            headers = {
                'Authorization': settings.FILE_SERVICE['auth_token']
            }
            base_url = settings.FILE_SERVICE['api_url'].strip("/")
            relative_url = FileConfigs.FILES_URL.strip("/")
            url = "{}/{}/".format(
                base_url,
                relative_url,
            )
            try:
                res = requests.post(
                    url=url,
                    files=files,
                    data=mimes,
                    headers=headers,
                )
            except Exception:
                raise api_exceptions.APIException(
                    _("uploading files failed, try again later")
                )
            if res.ok:
                data = UploadFileSerializer(
                    data=res.json()['result'],
                    many=True,
                )
                if data.is_valid(raise_exception=True):
                    if any(('error' in r and r['error']) for r in data.data):
                        raise api_exceptions.Conflict409(
                            _(
                                "upload failed for one or more files. "
                                "check your files extensions and size "
                                "and try again"
                            )
                        )
                    return data.data
            else:
                raise_exceptions(res)

    @classmethod
    def download_file(cls, file_id):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': settings.FILE_SERVICE['auth_token']
        }
        base_url = settings.FILE_SERVICE['api_url'].strip("/")
        relative_url = FileConfigs.DOWNLOAD_URL.strip("/").format(
            file_id=file_id,
        )
        url = "{}/{}/".format(
            base_url,
            relative_url,
        )
        try:
            res = requests.get(
                url=url,
                headers=headers,
                timeout=5.0,
            )

            if res.ok:
                return res.content, res.headers
            else:
                raise_exceptions(res)
        except Exception as e:
            raise api_exceptions.APIException(e)

    @classmethod
    def get_file(cls, file_id):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': settings.FILE_SERVICE['auth_token']
        }
        try:
            base_url = settings.FILE_SERVICE['api_url'].strip("/")
            relative_url = FileConfigs.FILE_URL.strip("/").format(
                file_id=file_id,
            )
            url = "{}/{}/".format(
                base_url,
                relative_url,
            )
            res = requests.get(
                url=url,
                headers=headers,
                timeout=5.0,
            )
            if res.ok:
                return res
            else:
                raise_exceptions(res)
        except requests.exceptions.Timeout:
            raise api_exceptions.RequestTimeout408(
                detail="Timeout on connection to file service"
            )
