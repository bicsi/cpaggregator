from rest_framework.generics import RetrieveAPIView, ListAPIView

from api.serializers import ProfileSerializer
from data.models import UserProfile


class RetrieveCurrentUser(RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return UserProfile.objects.select_related('user', 'statistics').get(user=self.request.user)


class RetrieveUser(RetrieveAPIView):
    serializer_class = ProfileSerializer
    lookup_field = "user__username"
    lookup_url_kwarg = "user"
    queryset = UserProfile.objects.select_related('user', 'statistics')


class ListUserRank(ListAPIView):
    queryset = UserProfile.objects.order_by('statistics__rank').select_related('user', 'statistics')
    serializer_class = ProfileSerializer
