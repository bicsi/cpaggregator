from django.http import Http404
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from data.models import Submission, UserProfile
from .models import LadderTask, Ladder
from django.shortcuts import get_object_or_404


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
            "task": {
                "id": task.task.get_path(),
                "title": task.task.name_or_id(),
            },
            "startedOn": task.started_on,
        }
        if best_submissions:
            [best_submission] = best_submissions
            task_serialized['task'].update({
                "bestSubmission": {
                    "id": best_submission.submission_id,
                    "submittedOn": best_submission.submitted_on,
                }
            })
        if task.status == LadderTask.Status.NEW:
            del task_serialized['task']

        return Response(task_serialized)


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
                "task": {
                    "id": task.task.get_path(),
                    "title": task.task.name_or_id(),
                }
            }
            if task.status == LadderTask.Status.NEW:
                del task_serialized['task']
            tasks_serialized.append(task_serialized)

        current_level = len(tasks) + 1
        if tasks and not tasks[-1].is_finished:
            current_level -= 1

        ladder_serialized = {
            "tasks": tasks_serialized,
            "totalPoints": ladder.statistics.total_points,
            "rank": ladder.statistics.rank,
            "currentLevel": current_level,
            "profile": {
                "firstName": ladder.profile.first_name,
                "lastName": ladder.profile.last_name,
                "userName": ladder.profile.username,
            }
        }
        return Response(ladder_serialized)

