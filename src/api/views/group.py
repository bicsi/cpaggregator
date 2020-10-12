from django.contrib.auth.models import User
from django.http import Http404
from requests import Response
from rest_framework.generics import RetrieveAPIView, ListAPIView, get_object_or_404
from django.db.models import Count

from api.serializers import ProfileSerializer, GroupSerializer, GroupMemberSerializer, TaskSerializer, \
    AssignmentSerializer
from data.models import UserProfile, UserGroup, GroupMember
from info.models import Assignment, TaskSheetTask
from core.logging import log


def get_group_or_404(group_id: str, user: User):
    group: UserGroup = get_object_or_404(
        UserGroup.objects
        .select_related('author')
        .annotate(members_count=Count('members'))
        .annotate(assignments_count=Count('assignments')),
        group_id=group_id)
    if group.visibility == "PRIVATE" and not group.is_owned_by(user) and \
            not GroupMember.objects.filter(profile__user=user, group=group).exists():
        raise Http404()
    return group


class RetrieveGroup(RetrieveAPIView):
    serializer_class = GroupSerializer

    def get_object(self):
        return get_group_or_404(self.kwargs['group'], self.request.user)


class ListGroupMembers(ListAPIView):
    serializer_class = GroupMemberSerializer

    def get_queryset(self):
        group = get_group_or_404(self.kwargs['group'], self.request.user)
        return GroupMember.objects.filter(group=group)


class RetrieveUser(RetrieveAPIView):
    serializer_class = ProfileSerializer
    lookup_field = "user__username"
    lookup_url_kwarg = "user"
    queryset = UserProfile.objects.select_related('user', 'statistics')


class ListUserRank(ListAPIView):
    queryset = UserProfile.objects.order_by(
        'statistics__rank').select_related('user', 'statistics')
    serializer_class = ProfileSerializer


class ListAssignments(ListAPIView):
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        group = get_group_or_404(self.kwargs['group'], self.request.user)
        return Assignment.objects.filter(group=group).select_related('sheet')


class ListGroups(ListAPIView):
    serializer_class = GroupSerializer

    def get_queryset(self):
        return (UserGroup.public
                .annotate(members_count=Count('members'))
                .annotate(assignments_count=Count('assignments'))
                .order_by('-members_count').all())
