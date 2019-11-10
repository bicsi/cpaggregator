import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django_ajax.mixin import AJAXMixin
from rest_framework.response import Response
from rest_framework.views import APIView

from core import urlparsers
from core.logging import log
from data.models import Task, TaskSource, Submission, Judge
from info import forms
from info.models import TaskSheetTask, TaskSheet, Assignment
from info.tables import ResultsTable
from info.views.generic import SubmissionDownloadCSVView


class DownloadResultsView(SubmissionDownloadCSVView):
    def get_queryset(self):
        assignment = Assignment.objects \
            .select_related('group', 'sheet') \
            .get(group__group_id=self.kwargs['group_id'],
                 sheet__sheet_id=self.kwargs['sheet_id'])
        return assignment.get_best_submissions()


class ResultsDetailView(generic.DetailView):
    template_name = 'info/results_detail.html'
    model = Assignment
    table = None
    submissions = None
    show_results = None
    show_submissions = None
    context_object_name = 'assignment'

    def get_object(self, **kwargs):
        obj = Assignment.objects \
            .select_related('group', 'sheet') \
            .get(group__group_id=self.kwargs['group_id'],
                 sheet__sheet_id=self.kwargs['sheet_id'])
        self.submissions = obj.get_best_submissions()
        self.table = ResultsTable(self.submissions.select_related(
            'task', 'task__judge', 'author__user', 'author__user__user'))
        return obj

    def get_context_data(self, **kwargs):
        request_user = self.request.user
        request_profile = request_user.profile
        kwargs['table'] = self.table
        kwargs['media'] = forms.AssignmentUpdateForm().media
        context = super(ResultsDetailView, self).get_context_data(**kwargs)

        submissions_for_user_and_task = {
            (submission.author.user, submission.task): submission
            for submission in self.submissions.select_related('author__user', 'task', 'task__judge')}

        # Map task to verdict of current user.
        verdict_for_user_dict = {
            submission.task: submission.verdict for ((user, task), submission) in
            submissions_for_user_and_task.items() if user == request_profile
        }
        # Build tasks as a dict.
        tasks = [{'task': task.task, 'verdict_for_user': verdict_for_user_dict.get(task.task)}
                 for task in TaskSheetTask.objects.select_related('task', 'task__judge') \
                     .filter(sheet=self.object.sheet).all()]

        # Send results data.
        results_data = []

        for user in self.object.group.members.all():
            user_submissions = []
            has_one_submission = False
            total_solved = 0
            for task in tasks:
                submission = submissions_for_user_and_task.get((user, task['task']), None)
                if submission:
                    user_submissions.append(submission)
                    has_one_submission = True
                    if submission.verdict == 'AC':
                        total_solved += 1
                else:
                    user_submissions.append(None)
            if has_one_submission:
                results_data.append({
                    'user': user,
                    'results': user_submissions,
                    'total_solved': total_solved,
                })
        results_data.sort(key=lambda x: x['total_solved'], reverse=True)

        context['tasks'] = tasks
        context['is_owner'] = self.object.sheet.is_owned_by(request_user)
        context['results'] = results_data
        context['show_results'] = self.show_results
        context['show_submissions'] = self.show_submissions

        return context


class SheetDetailView(generic.DetailView):
    template_name = 'info/sheet_detail.html'
    model = TaskSheet
    context_object_name = 'sheet'
    submissions = None
    show_all = False
    table = None

    def get_object(self, **kwargs):
        obj = TaskSheet.objects.get(sheet_id=self.kwargs['sheet_id'])

        if self.show_all:
            self.submissions = Submission.objects \
                .filter(author__user__user=self.request.user) \
                .filter(task__in=obj.tasks.all())
        else:
            self.submissions = Submission.objects.best() \
                .filter(author__user__user=self.request.user) \
                .filter(task__in=obj.tasks.all())

        self.table = ResultsTable(self.submissions)
        return obj

    def get_context_data(self, **kwargs):
        # Map task to verdict of current user.
        verdict_for_user_dict = {
            submission.task: submission.verdict for submission in
            self.submissions.filter(author__user__user=self.request.user)
        }
        # Build tasks as a dict.
        tasks = [{'task': task, 'verdict_for_user': verdict_for_user_dict.get(task)}
                 for task in self.object.tasks.all()]
        kwargs['tasks'] = tasks
        kwargs['show_all'] = self.show_all
        kwargs['is_owner'] = self.object.is_owned_by(self.request.user)
        kwargs['table'] = self.table

        return super(SheetDetailView, self).get_context_data(**kwargs)


class SheetTaskDeleteView(LoginRequiredMixin, SingleObjectMixin, generic.View):
    model = TaskSheet
    slug_field = 'sheet_id'
    slug_url_kwarg = 'sheet_id'

    def post(self, request, *args, **kwargs):
        sheet = self.get_object()
        if not sheet.is_owned_by(request.user):
            return HttpResponseForbidden()

        task = get_object_or_404(TaskSheetTask,
                                 sheet=sheet,
                                 task__task_id=request.POST.get('task_id', ''),
                                 task__judge__judge_id=request.POST.get('judge_id', ''))
        task.delete()
        return redirect(self.request.META.get('HTTP_REFERER', reverse_lazy('home')))


class SheetCreateView(LoginRequiredMixin, AJAXMixin, generic.FormView):
    model = TaskSheet
    form_class = forms.SheetCreateForm
    template_name = 'info/modal/sheet_create.html'
    sheet = None

    def get_form_kwargs(self):
        kwargs = super(SheetCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.sheet = form.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('sheet-detail', kwargs=dict(sheet_id=self.sheet.sheet_id))


class SheetTaskAddView(LoginRequiredMixin, SingleObjectMixin,
                       AJAXMixin, generic.FormView):
    form_class = forms.SheetTaskCreateForm
    template_name = 'info/modal/sheet_task_add.html'
    object = None

    def get_context_data(self, **kwargs):
        kwargs['object'] = self.object
        kwargs['judges'] = Judge.objects.filter(judge_id__in=[
            parser.judge_id for parser in urlparsers.TASK_PARSERS])
        return super(SheetTaskAddView, self).get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(TaskSheet, sheet_id=self.kwargs['sheet_id'])
        if not self.object.is_owned_by(request.user):
            return HttpResponseForbidden()
        return super(SheetTaskAddView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        task_url = form.cleaned_data['task_url']
        parse_result = urlparsers.parse_task_url(task_url)
        if not parse_result:
            messages.add_message(self.request, messages.ERROR, 'Could not parse task from url.')
        else:
            log.info(parse_result)
            judge = Judge.objects.get(judge_id=parse_result.judge_id)
            task, _ = Task.objects.get_or_create(
                judge=judge,
                task_id=parse_result.task_id.lower(),
            )
            TaskSheetTask.objects.create(
                task=task,
                sheet=self.object,
            )
            messages.add_message(self.request, messages.SUCCESS,
                                 f'Task __{task.name_or_id()}__ added successfully!')
        return redirect(self.request.META.get('HTTP_REFERER', reverse_lazy('home')))


class SheetDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = 'index.html'
    model = TaskSheet
    success_url = reverse_lazy('home')
    slug_url_kwarg = 'sheet_id'
    slug_field = 'sheet_id'

    def delete(self, request, *args, **kwargs):
        if not self.get_object().is_owned_by(request.user):
            return HttpResponseForbidden()
        return super(SheetDeleteView, self).delete(request, *args, **kwargs)


class SheetDescriptionUpdateView(LoginRequiredMixin, AJAXMixin, generic.UpdateView):
    template_name = 'info/modal/sheet_description_update.html'
    model = TaskSheet
    slug_url_kwarg = 'sheet_id'
    slug_field = 'sheet_id'
    form_class = forms.SheetDescriptionUpdateForm

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse_lazy('home'))

    def get_form_kwargs(self):
        kwargs = super(SheetDescriptionUpdateView, self).get_form_kwargs()
        kwargs['auto_id'] = False
        return kwargs

    def form_valid(self, form):
        if not self.object.is_owned_by(self.request.user):
            return HttpResponseForbidden()
        return super(SheetDescriptionUpdateView, self).form_valid(form)


class SheetTaskOrderingUpdate(APIView):
    def post(self, request, *args, **kwargs):
        sheet_id = kwargs['sheet_id']
        ordering = json.loads(request.data.get('ordering'))
        ordering_index = {int(elem): int(idx) for idx, elem in enumerate(ordering)}

        sheet = get_object_or_404(TaskSheet, sheet_id=sheet_id)
        if not sheet.is_owned_by(request.user):
            return HttpResponseForbidden()
        for idx, task in enumerate(TaskSheetTask.objects.filter(sheet=sheet).all()):
            task.ordering_id = ordering_index.get(idx)
            task.save()
        return Response({'success': 'Success'})


class AssignmentUpdateView(LoginRequiredMixin, AJAXMixin, generic.UpdateView):
    template_name = 'info/modal/assignment_update.html'
    model = Assignment
    form_class = forms.AssignmentUpdateForm

    def get_success_url(self):
        return reverse_lazy('group-sheet-detail', kwargs=self.kwargs)

    def get_object(self, queryset=None):
        return Assignment.objects.get(
            sheet__sheet_id=self.kwargs['sheet_id'],
            group__group_id=self.kwargs['group_id'])

    def form_valid(self, form):
        if not self.object.group.is_owned_by(self.request.user):
            return HttpResponseForbidden()
        return super(AssignmentUpdateView, self).form_valid(form)



