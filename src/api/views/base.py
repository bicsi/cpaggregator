from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from data.models import UserProfile, UserHandle, Judge
from api.serializers import ProfileSerializer


class RetrieveCurrentUser(RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return UserProfile.objects.select_related('user', 'statistics').get(user=self.request.user)


class RetrieveUser(RetrieveAPIView):
    serializer_class = ProfileSerializer
    lookup_field = "user__username"
    lookup_url_kwarg = "user"
    queryset = UserProfile.objects.select_related('user')


class ListJudges(APIView):
    def get(self, *args, **kwargs):
        return Response(Judge.objects.values_list('judge_id', flat=True))
