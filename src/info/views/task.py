from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django_ajax.mixin import AJAXMixin

from core.logging import log
from data.models import Submission, Task, UserHandle, MethodTag
from info.forms import TaskCustomTagCreateForm
from info.models import FavoriteTask, CustomTaskTag
from search.queries import search_task


class TaskListView(LoginRequiredMixin, generic.ListView):
    template_name = 'info/task_list.html'
    paginate_by = 10
    context_object_name = 'task_list'

    def get_queryset(self):
        queryset = Task.objects

        if self.request.GET.get('q'):
            queryset = search_task(self.request.GET['q'])
        if self.request.GET.get('ctag'):
            task_tags = CustomTaskTag.objects \
                .filter(profile=self.request.user.profile) \
                .filter(name=self.request.GET['ctag']) \
                .values_list('task', flat=True)
            queryset = queryset.filter(pk__in=task_tags)
        if self.request.GET.get('tag'):
            tag = MethodTag.objects.get(tag_id=self.request.GET['tag'])
            queryset = queryset.filter(tags=tag)

        return queryset.order_by(
            F('statistics__difficulty_score').asc(nulls_last=True),
            'name')

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
        context['default_tags'] = MethodTag.objects.all()
        context['custom_tags'] = CustomTaskTag.objects \
            .filter(profile=self.request.user.profile) \
            .values_list('name', flat=True).distinct()

        return context


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = 'info/task_detail.html'
    context_object_name = 'task'
    model = Task

    def get_object(self, queryset=None):
        return Task.objects.filter_path(self.kwargs['task_path']).get()

    def get_context_data(self, **kwargs):
        task = self.object
        kwargs['best_submission_for_user'] = Submission.objects.best().filter(
            task=task, author__user__user=self.request.user).first()
        kwargs['accepted_submissions'] = Submission.objects.best().filter(
            task=task, verdict='AC').select_related('author__user__user')
        kwargs['user_has_handle'] = UserHandle.objects.filter(
            judge=task.judge, user=self.request.user.profile
        ).exists()
        kwargs['custom_tags'] = CustomTaskTag.objects.filter(
            task=task, profile=self.request.user.profile).all()
        kwargs['is_favorited'] = self.request.user.profile.favorite_tasks.filter(
            task=task).exists()
        return super(TaskDetailView, self).get_context_data(**kwargs)


class TaskPreviewView(LoginRequiredMixin, AJAXMixin, generic.DetailView):
    template_name = 'info/modal/task_preview.html'
    context_object_name = 'task'
    model = Task

    def get_object(self, queryset=None):
        return Task.objects.filter_path(self.kwargs['task_path']).get()

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
        task = Task.objects.filter_path(self.kwargs['task_path']).get()

        queryset = FavoriteTask.objects.filter(profile=user.profile, task=task)
        if queryset.exists():
            queryset.delete()
        else:
            FavoriteTask.objects.create(profile=user.profile, task=task)

        return redirect('task-detail', task_path=self.kwargs['task_path'])


class TagCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = TaskCustomTagCreateForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def form_valid(self, form):
        task = Task.objects.filter_path(self.kwargs['task_path']).get()
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
        return reverse_lazy('task-detail', kwargs={self.kwargs['task_path']})

    def get_object(self, queryset=None):
        user = self.request.user.profile
        task = Task.objects.filter_path(self.kwargs['task_path']).get()
        name = self.kwargs['tag_name']
        return CustomTaskTag.objects.get(profile=user, task=task, name=name)
