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
    AssignmentSerializer, ProfileSerializerTiny, SubmissionSerializer
from data.models import UserProfile, UserGroup, GroupMember
from info.models import Assignment, TaskSheetTask
from core.logging import log
from rest_framework import permissions, serializers
from django.utils import timezone
from data.models import Submission
from django.db import connection


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
            'profile__user__username').select_related('profile', 'profile__user')

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


class ListResults(ListAPIView):
    def get_queryset(self):
        assignment = get_object_or_404(
            Assignment,
            group__group_id=self.kwargs['group'],
            sheet__sheet_id=self.kwargs['sheet'])
        self.assignment = assignment
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, sum(score) as total_score,
                RANK () OVER ( 
                    ORDER BY sum(score) DESC
                ) rank
                FROM (
                    SELECT DISTINCT data_submission.task_id as task_id, data_userhandle.user_id as id, info_tasksheet_x_task.score as score 
                    FROM data_submission
                    INNER JOIN info_tasksheet_x_task ON data_submission.task_id = info_tasksheet_x_task.task_id
                    INNER JOIN data_userhandle ON data_submission.author_id = data_userhandle.id
                    INNER JOIN data_groupmember ON data_groupmember.profile_id = data_userhandle.user_id
                    WHERE group_id = %s AND sheet_id = %s AND verdict = 'AC' AND submitted_on < %s
                ) AS results
                GROUP BY id;
            """, [assignment.group.pk, assignment.sheet.pk, assignment.end_on or timezone.now()])
            return cursor.fetchall()

    def serialize_data(self, results):
        assignment = self.assignment
        pks = [res[0] for res in results]

        # Get profiles.
        profile_for_pk = {
            profile.pk: profile for profile in 
                UserProfile.objects.filter(
                    pk__in=pks).select_related('user')}

        # Get best submissions.
        submissions = Submission.objects.filter(
            submitted_on__lte=assignment.end_on or timezone.now(),
            author__user__in=pks,
            task__in=TaskSheetTask.objects.filter(
                sheet=assignment.sheet).values_list('task', flat=True),
        ).select_related('author', 'author__user', 'author__user__user',
                         'task', 'task__statistics', 'task__judge').best()
        submissions_for_pk = {pk: [] for pk in pks}
        for sub in submissions:
            submissions_for_pk[sub.author.user.pk].append(sub)
        
        # Construct data.
        data = []
        for pk, total_score, rank in results:
            submissions = SubmissionSerializer(
                    submissions_for_pk[pk], many=True, 
                    include_author=False).data
            profile = ProfileSerializerTiny(profile_for_pk[pk]).data
            data.append({
                'submissions': submissions,
                'rank': rank,
                'total_score': total_score,
                'profile': profile,
            })

        return data

    def list(self, request, *args, **kwargs):
        raw_data = self.get_queryset()

        page = self.paginate_queryset(raw_data)
        if page:
            data = self.serialize_data(page)
            return self.get_paginated_response(data)

        return Response(self.serialize_data(list(raw_data)))
