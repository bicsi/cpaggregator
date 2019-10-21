from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django_ajax.mixin import AJAXMixin

from data.models import Submission, Task, UserHandle
from info.forms import TaskCustomTagCreateForm
from info.models import FavoriteTask, CustomTaskTag


class TaskListView(LoginRequiredMixin, generic.ListView):
    template_name = 'info/task_list.html'
    paginate_by = 10
    context_object_name = 'task_list'
    queryset = Task.objects.order_by(
        F('statistics__difficulty_score').asc(nulls_last=True))

    def get_context_data(self, *args, **kwargs):
        kwargs['task_count'] = self.get_queryset().count()
        context = super(TaskListView, self).get_context_data(*args, **kwargs)
        task_list = context.pop('task_list')
        # Map task to verdict of current user.
        verdict_for_user_dict = {
            submission.task: submission.verdict for submission in
            Submission.objects.best()
                .filter(author__user__user=self.request.user,
                        task__in=task_list)
        }
        favorite_tasks = {favorite.task for favorite in
                          self.request.user.profile.favorite_tasks.all()}
        context['task_list'] = [{
            'task': task,
            'verdict_for_user': verdict_for_user_dict.get(task),
            'faved': task in favorite_tasks,
        } for task in task_list]
        return context


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = 'info/task_detail.html'
    context_object_name = 'task'
    model = Task

    def get_object(self, queryset=None):
        return get_object_or_404(
            Task,
            task_id=self.kwargs['task_id'],
            judge__judge_id=self.kwargs['judge_id'],
        )

    def get_context_data(self, **kwargs):
        task = self.object
        kwargs['best_submission_for_user'] = Submission.objects.best().filter(
            task=task, author__user__user=self.request.user).first()
        kwargs['accepted_submissions'] = Submission.objects.best().filter(
            task=task, verdict='AC').select_related('author__user__user')
        kwargs['user_has_handle'] = UserHandle.objects.filter(
            judge=task.judge, user=self.request.user.profile
        ).exists()
        kwargs['is_favorited'] = self.request.user.profile.favorite_tasks.filter(
            task=task).exists()
        return super(TaskDetailView, self).get_context_data(**kwargs)


class TaskPreviewView(LoginRequiredMixin, AJAXMixin, generic.DetailView):
    template_name = 'info/modal/task_preview.html'
    context_object_name = 'task'
    model = Task

    def get_object(self, queryset=None):
        return get_object_or_404(
            Task,
            task_id=self.kwargs['task_id'],
            judge__judge_id=self.kwargs['judge_id'],
        )

    def get_context_data(self, **kwargs):
        task = self.object
        kwargs['best_submission_for_user'] = Submission.objects.best().filter(
            task=task, author__user__user=self.request.user).first()
        kwargs['accepted_submissions'] = Submission.objects.best().filter(
            task=task, verdict='AC')
        kwargs['user_has_handle'] = UserHandle.objects.filter(
            judge=task.judge, user=self.request.user.profile
        ).exists()
        kwargs['is_favorited'] = self.request.user.profile.favorite_tasks.filter(
            task=task).exists()
        return super(TaskPreviewView, self).get_context_data(**kwargs)


class FavoriteToggleView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        user = request.user
        task = get_object_or_404(
            Task,
            judge__judge_id=self.kwargs['judge_id'],
            task_id=self.kwargs['task_id'])

        queryset = FavoriteTask.objects.filter(profile=user.profile, task=task)
        if queryset.exists():
            queryset.delete()
        else:
            FavoriteTask.objects.create(profile=user.profile, task=task)

        return redirect('task-detail', judge_id=task.judge.judge_id, task_id=task.task_id)


class TagCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = TaskCustomTagCreateForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def form_valid(self, form):
        task = get_object_or_404(Task, judge__judge_id=self.kwargs['judge_id'], task_id=self.kwargs['task_id'])
        tag = form.save(commit=False)
        tag.task = task
        tag.profile = self.request.user.profile
        try:
            tag.save()
        except IntegrityError:
            pass

        return redirect('task-detail', judge_id=self.kwargs['judge_id'], task_id=self.kwargs['task_id'])

    def form_invalid(self, form):
        return redirect('task-detail', judge_id=self.kwargs['judge_id'], task_id=self.kwargs['task_id'])


class TagDeleteView(LoginRequiredMixin, generic.DeleteView):
    def get_success_url(self):
        return reverse_lazy('task-detail', kwargs=dict(
            judge_id=self.kwargs['judge_id'], task_id=self.kwargs['task_id']))

    def get_object(self, queryset=None):
        user = self.request.user.profile
        task = get_object_or_404(Task, judge__judge_id=self.kwargs['judge_id'], task_id=self.kwargs['task_id'])
        name = self.kwargs['tag_name']
        return CustomTaskTag.objects.get(profile=user, task=task, name=name)
