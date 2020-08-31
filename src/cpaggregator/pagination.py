from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ResultsPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'prev': self.get_previous_link(),
            },
            'count': self.page.paginator.count,
            'page_count': self.page.paginator.num_pages,
            'page_size': self.get_page_size(self.request),
            'results': data,
        })

