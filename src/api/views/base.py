from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from data.models import UserProfile, UserHandle, Judge, Submission
from api.serializers import ProfileSerializer, SubmissionSerializer


class ListUserBestSubmissions(ListAPIView):
    filter_ac = False
    exclude_ac = False
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        queryset = (
            Submission.objects.best()
                .filter(author__user__user__username=self.kwargs['user'])
                .select_related('task', 'author', 'task__judge', 'task__statistics'))
        if self.filter_ac:
            queryset = queryset.filter(verdict='AC')
        if self.exclude_ac:
            queryset = queryset.exclude(verdict='AC')
        return queryset


class ListJudges(APIView):
    def get(self, *args, **kwargs):
        return Response(Judge.objects.values_list('judge_id', flat=True))
