from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.pagination import LimitOffsetPagination


def is_iterable(obj):
    try:
        for _ in obj:
            break
    except TypeError:
        return False

    return True


class RespinaSerializer(object):
    def __init__(self, model):
        self.model = model

    def get_dict(self):
        raise NotImplementedError

    @classmethod
    def serialize(cls, request, queryset=None, is_list=True, one_object=None, *args, **kwargs):
        paginator = None

        if one_object:
            is_list = False

        if is_list:
            paginator = LimitOffsetPagination()
            items = paginator.paginate_queryset(queryset=queryset, request=request)

            data = []
            for item in items:
                data.append(cls(item, *args, **kwargs).get_dict())

        else:
            item = one_object if one_object else queryset.get()
            data = cls(item, *args, **kwargs).get_dict()

        return data, paginator


class ContentTypeSerializer(serializers.ModelSerializer):
    """
    This Is a General & Reusable Serializer for Django ContentType Model.
    """

    def __init__(self, *args, **kwargs):
        super(ContentTypeSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = ContentType
        fields = (
            'id',
            'app_label',
            'model',
        )
