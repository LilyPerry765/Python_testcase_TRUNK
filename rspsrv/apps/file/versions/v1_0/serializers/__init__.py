from datetime import datetime

from django import forms
from rest_framework import serializers


class UploadFileForm(forms.Form):
    file = forms.FileField()


class FileSerializer(serializers.Serializer):
    id = serializers.CharField()
    mimeType = serializers.CharField()
    fileSize = serializers.IntegerField()
    createdAt = serializers.CharField()
    originalFilename = serializers.CharField()

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            "id": instance["id"],
            "mime_type": instance["mimeType"],
            "file_size": instance["fileSize"],
            "created_at": datetime.strptime(
                instance["createdAt"],
                '%Y-%m-%dT%H:%M:%S.%fZ',
            ).timestamp(),
            "filename": instance["originalFilename"],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UploadFileSerializer(serializers.Serializer):
    originalFilename = serializers.CharField(required=False)
    id = serializers.CharField(required=False, allow_null=True)
    error = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def to_representation(self, instance):
        if instance['id']:
            return {
                "filename": instance['originalFilename'],
                "id": instance['id'],
            }
        else:
            return {
                "filename": instance['originalFilename'],
                "error": instance['error'],
            }
