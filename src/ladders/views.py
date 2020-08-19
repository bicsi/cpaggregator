import datetime
import random
from random import randint

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django_ajax.mixin import AJAXMixin

from data.models import UserProfile, UserHandle, Task, Submission
from .models import LadderTask, Ladder
from core.logging import log

# Create your views here.


def generate_new_task(ladder, commit=True):
    profile = ladder.profile
    handles = list(UserHandle.objects.filter(user=profile).select_related('judge'))
    previous_tasks = set(ladder.tasks.values_list('task', flat=True))
    judges = {handle.judge for handle in handles}

    tried_tasks = set(Submission.objects
                       .filter(author__in=handles)
                       .values_list('task', flat=True)
                       .distinct())
    forbidden_tasks = tried_tasks | previous_tasks
    available_tasks = [task for task in Task.objects.filter(judge__in=judges)
                       if task.pk not in forbidden_tasks]

    if not available_tasks:
        return None

    chosen_task = random.choice(available_tasks)
    duration = datetime.timedelta(minutes=120)
    ladder_task = LadderTask(
        ladder=ladder,
        task=chosen_task,
        duration=duration,
        status=LadderTask.Status.NEW)

    if commit:
        ladder_task.save()
    return ladder_task


class LaddersDashboard(LoginRequiredMixin, generic.TemplateView):
    template_name = 'ladders/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super(LaddersDashboard, self).get_context_data(**kwargs)
        profile = self.request.user.profile

        ladder, _ = Ladder.objects.get_or_create(profile=profile)
        ladder_tasks = list(LadderTask.objects.filter(ladder=ladder))

        next_level = 1 + len(ladder_tasks)
        current_level = (next_level
                         if not ladder_tasks or ladder_tasks[-1].is_finished
                         else next_level - 1)

        if current_level != next_level:
            current_task = ladder_tasks[-1]

            # Check if it was expired or solved
            ac_submissions = list(
                Submission.objects
                    .filter(task=current_task.task,
                            author__user=profile,
                            verdict='AC')
                    .order_by('submitted_on')[:1])
            if ac_submissions and (not current_task.started_on or
                                   current_task.started_on + current_task.duration >
                                   ac_submissions[0].submitted_on):
                current_task.status = LadderTask.Status.COMPLETED
                current_task.save()
                current_level += 1
            elif (current_task.started_on and current_task.started_on +
                  current_task.duration < timezone.now()):
                current_task.status = LadderTask.Status.EXPIRED
                current_task.save()
                current_level += 1

        if current_level == next_level:
            current_task = generate_new_task(ladder, next_level)
            if current_task:
                ladder_tasks.append(current_task)
                next_level += 1

        required_len = max(len(ladder_tasks) + 12, 100)
        required_len += (12 - required_len % 12) % 12

        while len(ladder_tasks) < required_len:
            ladder_tasks.append({"status": LadderTask.Status.LOCKED})

        ctx.update({
            'ladder_tasks': ladder_tasks,
            'current_level': current_level,
        })
        return ctx


class LadderTaskDetail(LoginRequiredMixin, AJAXMixin, generic.DetailView):
    template_name = 'ladders/modal/ladder_task_preview.html'
    model = LadderTask
    pk_url_kwarg = 'task'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        ctx = super(LadderTaskDetail, self).get_context_data(**kwargs)

        task = self.object
        tasks = LadderTask.objects.filter(ladder=task.ladder)
        if task.started_on:
            tasks = tasks.filter(started_on__lte=task.started_on)
        ctx['level'] = tasks.count()

        if task.status == LadderTask.Status.COMPLETED:
            ac_submission = (
                Submission.objects
                    .filter(task=task.task, author__user=task.ladder.profile, verdict='AC')
                    .order_by('submitted_on')[:1])
            if ac_submission and ac_submission[0].submitted_on > task.started_on:
                ctx['completed_in'] = ac_submission[0].submitted_on - task.started_on

        return ctx


class LadderTaskStart(LoginRequiredMixin, SingleObjectMixin, generic.RedirectView):
    pk_url_kwarg = 'task'
    model = LadderTask

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        if task.ladder.profile != request.user.profile or task.status != LadderTask.Status.NEW:
            raise Http404()
        task.started_on = timezone.now()
        task.status = LadderTask.Status.RUNNING
        task.save()
        return redirect('ladders:dashboard')
