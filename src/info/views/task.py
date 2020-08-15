from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import F
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic
from django_ajax.mixin import AJAXMixin

from data.models import Submission, Task, UserHandle, MethodTag, TaskStatement
from info import forms
from info.forms import TaskCustomTagCreateForm
from info.models import FavoriteTask, CustomTaskTag
from scraper.services import scrape_task_info, scrape_submissions_for_tasks
from search.queries import search_task


class TaskListView(LoginRequiredMixin, generic.ListView):
    template_name = 'info/task_list.html'
    paginate_by = 50
    context_object_name = 'task_list'

    def get_queryset(self):
        queryset = Task.objects.select_related('statistics')

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
            submission['task']: submission['verdict']
            for submission in Submission.objects.best()
                .filter(author__user__user=self.request.user,
                        task__in=task_list)
                .values("task", "verdict")
        }

        favorite_tasks = set(
            self.request.user.profile.favorite_tasks.all()
                .values_list('task', flat=True))

        context['task_list'] = [{
            'task': task,
            'verdict_for_user': verdict_for_user_dict.get(task.pk),
            'faved': task.pk in favorite_tasks,
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

        return redirect('task-detail', **self.kwargs)


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

        return redirect('task-detail', **self.kwargs)

    def form_invalid(self, form):
        return redirect('task-detail', **self.kwargs)


class TagDeleteView(LoginRequiredMixin, generic.DeleteView):
    def get_success_url(self):
        return reverse_lazy('task-detail', kwargs={
            "task_path": self.kwargs["task_path"]})

    def get_object(self, queryset=None):
        user = self.request.user.profile
        task = Task.objects.filter_path(self.kwargs['task_path']).get()
        name = self.kwargs['tag_name']
        return CustomTaskTag.objects.get(profile=user, task=task, name=name)


class TaskStatementUpdateView(LoginRequiredMixin, AJAXMixin, generic.UpdateView):
    template_name = 'info/modal/task_statement_update.html'
    context_object_name = 'task_statement'
    model = TaskStatement
    form_class = forms.TaskStatementUpdateForm

    def get_success_url(self):
        return reverse_lazy("task-detail", kwargs=self.kwargs)

    def get_object(self, queryset=None):
        if not self.request.user.is_superuser:
            raise Http404()
        return Task.objects.filter_path(self.kwargs['task_path']).get().statement


class TaskStatementScrapeView(LoginRequiredMixin, generic.View):
    model = TaskStatement

    def post(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise Http404()
        task = Task.objects.filter_path(kwargs['task_path']).get()
        scrape_task_info(task.get_path())
        return redirect("task-detail", **kwargs)


class TaskSubmissionsScrapeView(LoginRequiredMixin, generic.View):
    def post(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise Http404()
        scrape_submissions_for_tasks(kwargs['task_path'])
        return redirect("task-detail", **kwargs)
