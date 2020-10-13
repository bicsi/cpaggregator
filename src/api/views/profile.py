from rest_framework.generics import RetrieveAPIView, ListAPIView, UpdateAPIView, CreateAPIView, DestroyAPIView, GenericAPIView
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework import permissions

from api.serializers import ProfileSerializer, UserHandleSerializer
from data.models import UserProfile, UserHandle


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
    queryset = UserProfile.objects.order_by(
        'statistics__rank').select_related('user', 'statistics')
    serializer_class = ProfileSerializer


class CreateHandle(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserHandleSerializer

    def get_serializer_context(self):
        context = super(CreateHandle, self).get_serializer_context()
        context['user'] = self.request.user.profile
        return context


class RetrieveDestroyHandle(RetrieveAPIView, DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserHandleSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return UserHandle.objects.all()
        return UserHandle.objects.filter(user=self.request.user.profile)

    def get_object(self):
        return self.get_queryset().get(
            judge__judge_id=self.kwargs['judge_id'],
            handle=self.kwargs['handle'])
