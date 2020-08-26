from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ResultsPagination(PageNumberPagination):
    page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'prev': self.get_previous_link(),
            },
            'count': self.page.paginator.count,
            'page_count': self.page.paginator.num_pages,
            'page_size': self.page_size,
            'results': data,
        })

