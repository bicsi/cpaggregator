from django.http import Http404
from rest_framework.generics import ListAPIView

from data.models import Submission
from api import serializers


class ListBestSubmissions(ListAPIView):
    def get_queryset(self):
        return (Submission.objects.best()
                .filter(author__user__user__username=self.kwargs['user'])
                .select_related('task', 'author'))

    serializer_class = serializers.SubmissionSerializer

