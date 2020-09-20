import datetime
import random
from random import randint

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django_ajax.mixin import AJAXMixin

from data.models import UserProfile, UserHandle, Task, Submission, Judge
from stats.services import compute_ladder_statistics
from .models import LadderTask, Ladder
from core.logging import log
from .services import update_ladder

# Create your views here.


class LaddersDashboard(LoginRequiredMixin, generic.TemplateView):
    template_name = 'ladders/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super(LaddersDashboard, self).get_context_data(**kwargs)
        profile = self.request.user.profile

        ladder, _ = Ladder.objects.get_or_create(profile=profile)
        ladder_tasks, current_task = update_ladder(ladder)
        current_level = len(ladder_tasks)

        required_len = max(len(ladder_tasks) + 12, 100)
        required_len += (12 - required_len % 12) % 12

        while len(ladder_tasks) < required_len:
            ladder_tasks.append({"status": LadderTask.Status.LOCKED})

        ctx.update({
            'ladder_tasks': ladder_tasks,
            'current_level': current_level,
            'current_task': current_task,
            'ladder': ladder,
            'all_judges': Judge.objects.all(),
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

        try:
            ctx['best_submission_for_user'] = (Submission.objects.best()
                .get(author__user=self.request.user.profile, task=task.task))
        except ObjectDoesNotExist:
            ctx['best_submission_for_user'] = None

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
        task.start()
        return redirect('ladders:dashboard')


class LadderRankListView(generic.ListView):
    template_name = 'ladders/rank_list.html'
    paginate_by = 10
    context_object_name = 'ladder_list'
    queryset = Ladder.objects.order_by('statistics__rank').select_related('profile', 'statistics')

    def get_context_data(self, **kwargs):
        kwargs['user_count'] = Ladder.objects.count()
        return super(LadderRankListView, self).get_context_data(**kwargs)
