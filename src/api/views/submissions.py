from django.http import Http404
from rest_framework.generics import ListAPIView

from api.views.group import get_group_or_404
from data.models import Submission, UserGroup, GroupMember
from api import serializers
from info.models import TaskSheetTask, Assignment, Task


class ListSubmissions(ListAPIView):
    kind = 'best'

    def get_queryset(self):
        queryset = Submission.objects

        group_id = self.request.query_params.get('group')
        author_username = self.request.query_params.get('author')
        sheet_id = self.request.query_params.get('sheet')
        tasks = self.request.query_params.get('task')

        if author_username:
            queryset = queryset.filter(
                author__user__user__username=author_username)

        if tasks:
            tasks = tasks.replace(':', '/').lower()
            if '|' in tasks:
                tasks_set = {task for task in tasks.split('|')}
                tasks = Task.objects.filter(
                    task_id__in=[t.split('/', 1)[1] for t in tasks_set]).select_related('judge')
                tasks = [
                    t for t in tasks if "/".join([t.judge.judge_id, t.task_id]) in tasks_set]
                queryset = queryset.filter(task__in=tasks)
            else:
                judge_id, task_id = tasks.split('/', 1)
                queryset = queryset.filter(
                    task__judge__judge_id=judge_id, task__task_id=task_id)

        if group_id:
            group = get_group_or_404(group_id, self.request.user)
            members = GroupMember.objects.filter(
                group=group).values_list('profile')

            if sheet_id:
                tasks = TaskSheetTask.objects.filter(
                    sheet__sheet_id=sheet_id).values_list('task')
            else:
                assignments_queryset = Assignment.objects.filter(group=group)
                if not group.is_owned_by(self.request.user):
                    assignments_queryset = assignments_queryset.visible()

                sheets = assignments_queryset.values_list('sheet', flat=True)
                tasks = TaskSheetTask.objects.filter(
                    sheet__in=sheets).values_list('task')

            queryset = queryset.filter(
                author__user__in=members, task__in=tasks)

        if self.kind in ['best', 'solved', 'unsolved']:
            queryset = queryset.best()
        if self.kind == 'solved':
            queryset = queryset.filter(verdict='AC')
        if self.kind == 'unsolved':
            queryset = queryset.exclude(verdict='AC')
        return queryset.select_related('task', 'author', 'task__judge', 'author__user', 'author__user__user')

    serializer_class = serializers.SubmissionSerializer
