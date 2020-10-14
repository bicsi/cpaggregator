from django.contrib.auth.models import User
from django.http import Http404
from requests import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, RetrieveAPIView, ListAPIView, DestroyAPIView, CreateAPIView, RetrieveDestroyAPIView, ListCreateAPIView, get_object_or_404
from django.db.models import Count, When, Value, Case
from rest_framework.response import Response
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from rest_framework import status
from api.serializers import ProfileSerializer, GroupSerializer, GroupMemberSerializer, TaskSerializer, \
    AssignmentSerializer
from data.models import UserProfile, UserGroup, GroupMember
from info.models import Assignment, TaskSheetTask
from core.logging import log
from rest_framework import permissions, serializers


def get_group_or_404(group_id: str, user: User):
    try:
        group = (UserGroup.objects
                 .select_related('author')
                 .annotate(members_count=Count('members', distinct=True),
                           assignments_count=Count('assignments', distinct=True))
                 .get(group_id=group_id))
    except UserGroup.DoesNotExist:
        raise Http404()
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
        return GroupMember.objects.filter(group=group).order_by(
            Case(When(role='owner', then=Value(0)), default=Value(1)),
            'profile__user__username')


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
                .annotate(members_count=Count('members', distinct=True),
                          assignments_count=Count('assignments', distinct=True))
                .order_by('-members_count').all())


class RetrieveDestroyGroupMember(RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupMemberSerializer

    def get_queryset(self):
        group_id = self.kwargs['group']
        username = self.kwargs['username']
        group = get_group_or_404(group_id, self.request.user)
        if group.is_owned_by(self.request.user):
            return GroupMember.objects.filter(group=group)
        return GroupMember.objects.filter(group=group, profile__user=self.request.user)

        queryset = UserGroup.objects.filter(group=group)

    def get_object(self):
        return self.get_queryset().get(profile__user__username=self.kwargs['username'])


class CreateGroupMemberSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.ChoiceField(['member', 'owner'])


class ListCreateGroupMember(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateGroupMemberSerializer
        return GroupMemberSerializer

    def get_queryset(self):
        group = get_group_or_404(self.kwargs['group'], self.request.user)
        return GroupMember.objects.filter(group=group).order_by(
            Case(When(role='owner', then=Value(0)), default=Value(1)),
            'profile__user__username')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        profile = UserProfile.objects.select_related('user').get(
            user__username=data['username'])
        group = get_group_or_404(
            group_id=self.kwargs['group'], user=self.request.user)

        if not group.is_owned_by(self.request.user) and profile.username != self.request.user.username:
            return HttpResponseForbidden()
        if not group.is_owned_by(request.user) and data['role'] != 'member':
            return HttpResponseForbidden()

        member = GroupMember.objects.create(
            group=group, profile=profile, role=data['role'])
        serializer = GroupMemberSerializer(member)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
