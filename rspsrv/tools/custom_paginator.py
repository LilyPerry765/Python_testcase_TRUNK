from rest_framework.pagination import LimitOffsetPagination


class CustomPaginator(LimitOffsetPagination):
    def __init__(self, **kwargs):
        self.count = None
        self.limit = None
        self.offset = None
        self.request = None

    def paginate_queryset(self, queryset, request, view=None):
        self.count = queryset.count()
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return list(queryset[self.offset:self.offset + self.limit])

    def paginate(self, request, data):
        paginator = CustomPaginator()

        if 'bypass_pagination' in request.query_params:
            return data, None

        data = paginator.paginate_queryset(queryset=data, request=request)

        return data, paginator
