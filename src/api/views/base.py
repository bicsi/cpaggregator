from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from data.models import UserProfile, UserHandle, Judge, Submission
from api.serializers import ProfileSerializer, SubmissionSerializer


class RetrieveCurrentUser(RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return UserProfile.objects.select_related('user', 'statistics').get(user=self.request.user)


class RetrieveUser(RetrieveAPIView):
    serializer_class = ProfileSerializer
    lookup_field = "user__username"
    lookup_url_kwarg = "user"
    queryset = UserProfile.objects.select_related('user', 'statistics')


class ListUserBestSubmissions(ListAPIView):
    def get_queryset(self):
        return (Submission.objects.best()
                .filter(author__user__user__username=self.kwargs['user'])
                .select_related('task', 'author'))

    serializer_class = SubmissionSerializer


class ListJudges(APIView):
    def get(self, *args, **kwargs):
        return Response(Judge.objects.values_list('judge_id', flat=True))
