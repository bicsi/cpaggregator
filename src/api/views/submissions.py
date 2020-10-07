from django.http import Http404
from rest_framework.generics import ListAPIView

from api.views.group import get_group_or_404
from data.models import Submission, UserGroup
from api import serializers
from info.models import TaskSheetTask, Assignment


class ListSubmissions(ListAPIView):
    only_best = True

    def get_queryset(self):
        queryset = Submission.objects
        if self.only_best:
            queryset = queryset.best()

        author_username = self.request.query_params.get('author')
        if author_username:
            queryset = queryset.filter(author__user__user__username=author_username)

        group_id = self.request.query_params.get('group')
        if group_id:
            group = get_group_or_404(group_id, self.request.user)
            assignments_queryset = Assignment.objects.filter(group=group)
            if not group.is_owned_by(self.request.user):
                assignments_queryset = assignments_queryset.visible()

            sheets = assignments_queryset.values_list('sheet', flat=True)
            tasks = TaskSheetTask.objects.filter(sheet__in=sheets).values_list('task')
            queryset = queryset.filter(task__in=tasks)

        return queryset.select_related('task', 'author')

    serializer_class = serializers.SubmissionSerializer

