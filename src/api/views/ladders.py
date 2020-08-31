from django.http import Http404
from rest_framework import authentication, permissions
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from data.models import Submission, UserProfile
from ladders.models import LadderTask, Ladder
from django.shortcuts import get_object_or_404
from api import serializers


class ShowLadderTask(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, **kwargs):
        level = self.kwargs['level']
        profile = get_object_or_404(UserProfile.objects, user__username=self.kwargs['user'])
        ladder = get_object_or_404(Ladder.objects, profile=profile)

        if ladder.profile != self.request.user.profile and not self.request.user.is_superuser:
            self.permission_denied(request, message="Cannot view other people's ladder.")

        tasks = list(LadderTask.objects.filter(ladder=ladder).values_list('pk', flat=True))

        if level > len(tasks):
            raise Http404()

        task: LadderTask = LadderTask.objects.select_related('task').get(pk=tasks[level - 1])
        best_submissions = list(Submission.objects.best().filter(author__user=profile, task=task.task))

        task_serialized = {
            "level": level,
            "status": task.status,
            "task": serializers.TaskSerializer(task.task).data,
            "started_on": task.started_on,
            "judge_id": task.task.judge.judge_id,
            "duration": task.duration,
        }
        if best_submissions:
            [best_submission] = best_submissions
            task_serialized['task']['best_submission'] = {
                "submission_id": best_submission.submission_id,
                "submitted_on": best_submission.submitted_on,
                "verdict": best_submission.verdict,
            }
        else:
            task_serialized['task']['best_submission'] = None
        if task.status == LadderTask.Status.NEW:
            del task_serialized['task']

        return Response(task_serialized)


class ListBestSubmissions(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tasks = (LadderTask.objects.filter(ladder__profile__user__username=self.kwargs['user'])
                 .values_list('task', flat=True))
        print(tasks)
        return (Submission.objects.best()
                .filter(author__user__user__username=self.kwargs['user'], task__in=tasks)
                .select_related('task', 'author'))

    serializer_class = serializers.SubmissionSerializer


class ShowLadder(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, **kwargs):
        queryset = Ladder.objects.select_related('profile', 'statistics', 'profile__user')
        ladder = get_object_or_404(queryset, profile__user__username=self.kwargs['user'])
        if ladder.profile != self.request.user.profile and not self.request.user.is_superuser:
            self.permission_denied(request, message="Cannot view other people's ladder.")

        tasks = list(LadderTask.objects.filter(ladder=ladder).select_related('task'))

        tasks_serialized = []
        for idx, task in enumerate(tasks):
            task_serialized = {
                "level": idx + 1,
                "status": task.status,
                "task": serializers.TaskSerializer(task.task).data,
                "judge_id": task.task.judge.judge_id,
                "duration": task.duration,
                "started_on": task.started_on,
            }
            if task.status == LadderTask.Status.NEW:
                del task_serialized['task']
            tasks_serialized.append(task_serialized)

        current_level = len(tasks) + 1
        if tasks and not tasks[-1].is_finished:
            current_level -= 1

        ladder_serialized = {
            "tasks": tasks_serialized,
            "total_points": ladder.statistics.total_points,
            "rank": ladder.statistics.rank,
            "current_level": current_level,
            "profile": {
                "first_name": ladder.profile.first_name,
                "last_name": ladder.profile.last_name,
                "username": ladder.profile.username,
            }
        }
        return Response(ladder_serialized)


class ListLadderRank(ListAPIView):
    queryset = Ladder.objects.order_by('statistics__rank').select_related('profile', 'statistics')
    serializer_class = serializers.LadderSerializer

