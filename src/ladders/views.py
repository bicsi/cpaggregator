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


# Create your views here.


def generate_new_task(ladder, commit=True):
    profile = ladder.profile
    log.info(f"Generating new task for {profile}...")

    handles = list(UserHandle.objects.filter(user=profile).select_related('judge'))
    judges = {handle.judge for handle in handles}

    tried_tasks = set(Submission.objects
                      .filter(author__in=handles)
                      .values_list('task', flat=True)
                      .distinct())
    previous_tasks = set(ladder.tasks.values_list('task', flat=True))
    forbidden_tasks = tried_tasks | previous_tasks

    available_tasks = [
        task for task in Task.objects
            .filter(judge__in=judges, statistics__isnull=False)
            .select_related('statistics')
        if task.pk not in forbidden_tasks
           and task.statistics.users_solved_count >= 2]

    if not available_tasks:
        log.warning("Could not generate: no tasks to choose from.")
        return None

    solved_tasks_scores = [
        score for _, score in Submission.objects
            .filter(author__in=handles, verdict='AC')
            .values_list('task', 'task__statistics__difficulty_score')
            .distinct()
        if score is not None]

    bounds = 25, 60
    if len(solved_tasks_scores) >= 25:
        solved_tasks_scores.sort()
        solved_tasks_scores = solved_tasks_scores[-50:-5]
        mid_score = random.choice(solved_tasks_scores)
        bounds = mid_score * 0.9, mid_score * 1.1

    sought_score = random.randint(int(bounds[0]), int(bounds[1]))
    log.info(f"Sought score: {sought_score} (bounds: {bounds})")

    random.shuffle(available_tasks)
    best_error, chosen_task = None, None
    for task in available_tasks:
        curr_error = abs(task.statistics.difficulty_score - sought_score)
        if not chosen_task or best_error > curr_error:
            best_error, chosen_task = curr_error, task

    log.info(f"Chosen task: {chosen_task} (score: {chosen_task.statistics.difficulty_score})")
    duration = datetime.timedelta(minutes=120)
    ladder_task = LadderTask(
        ladder=ladder,
        task=chosen_task,
        duration=duration,
        status=LadderTask.Status.NEW)

    if commit:
        ladder_task.save()
    return ladder_task


def update_ladder(ladder):
    profile = ladder.profile
    ladder_tasks = list(LadderTask.objects.filter(ladder=ladder).select_related('task', 'task__statistics'))

    next_level = 1 + len(ladder_tasks)
    current_level = (next_level
                     if not ladder_tasks or ladder_tasks[-1].is_finished
                     else next_level - 1)

    current_task = None
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
        current_task = generate_new_task(ladder)
        if current_task:
            ladder_tasks.append(current_task)
            next_level += 1
        compute_ladder_statistics()

    return ladder_tasks, current_task


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
        task.started_on = timezone.now()
        task.status = LadderTask.Status.RUNNING
        task.save()
        return redirect('ladders:dashboard')


class LadderRankListView(generic.ListView):
    template_name = 'ladders/rank_list.html'
    paginate_by = 10
    context_object_name = 'ladder_list'
    queryset = Ladder.objects.order_by('statistics__rank').select_related('profile', 'statistics')

    def get_context_data(self, **kwargs):
        kwargs['user_count'] = Ladder.objects.count()
        return super(LadderRankListView, self).get_context_data(**kwargs)
