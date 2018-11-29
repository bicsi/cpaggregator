from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.datetime_safe import datetime
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from accounts.forms import UserForm
from info.forms import UserUpdateForm, HandleCreateForm
from . import forms
from info.models import TaskSheet, Assignment
from data.models import UserProfile, UserHandle, UserGroup, Task, User, Submission

from info.tables import ResultsTable
from django.contrib.messages.views import SuccessMessageMixin
from bootstrap_modal_forms.mixins import PassRequestMixin


class ProfileUpdateView(LoginRequiredMixin, PassRequestMixin,
                        SuccessMessageMixin, generic.UpdateView):
    template_name = 'info/update_profile.html'
    success_message = 'Success: User was updated.'
    success_url = reverse_lazy('me')
    model = UserProfile
    form_class = UserUpdateForm
    slug_url_kwarg = 'username'
    slug_field = 'username'

    def get_queryset(self):
        return super(ProfileUpdateView, self).get_queryset() \
            .filter(user=self.request.user)


class HandleCreateView(LoginRequiredMixin, PassRequestMixin, SuccessMessageMixin, generic.CreateView):
    template_name = 'info/create_handle.html'
    success_message = 'Success: Handle was created.'
    model = UserHandle
    success_url = reverse_lazy('me')
    form_class = HandleCreateForm

    def form_invalid(self, form):
        super(HandleCreateView, self).form_invalid(form)
        return redirect(self.success_url)

    def form_valid(self, form):
        super(HandleCreateView, self).form_valid(form)
        return redirect(self.success_url)


class HandleDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = UserHandle
    success_url = reverse_lazy('me')
    slug_url_kwarg = 'handle_id'
    slug_field = 'id'

    def get_queryset(self):
        return super(HandleDeleteView, self).get_queryset() \
            .filter(user__user=self.request.user)


class MeDetailView(LoginRequiredMixin, generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('profile', kwargs={
            'username': self.request.user.username})


class UserSubmissionsDetailView(generic.DetailView):
    template_name = 'info/user_submissions_detail.html'
    model = UserProfile
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        return UserProfile.objects.get(user__username=self.kwargs['username'])


class ResultsDetailView(generic.DetailView):
    template_name = 'info/results_detail.html'
    model = Assignment
    table = None
    submissions = None
    show_all = False
    context_object_name = 'assignment'

    def get_object(self, **kwargs):
        obj = Assignment.objects.get(group__group_id=self.kwargs['group_id'],
                                     sheet__sheet_id=self.kwargs['sheet_id'])
        if self.show_all:
            self.submissions = obj.get_all_submissions()
        else:
            self.submissions = obj.get_best_submissions()

        self.table = ResultsTable(self.submissions)
        return obj

    def get_context_data(self, **kwargs):
        kwargs['table'] = self.table
        context = super(ResultsDetailView, self).get_context_data(**kwargs)

        # Map task to verdict of current user.
        verdict_for_user_dict = {
            submission.task: submission.verdict for submission in
            self.submissions.filter(author__user__user=self.request.user)
        }
        # Build tasks as a dict.
        tasks = [{'task': task, 'verdict_for_user': verdict_for_user_dict.get(task)}
                 for task in self.object.sheet.tasks.all()]
        context['tasks'] = tasks
        context['show_all'] = self.show_all
        context['is_owner'] = self.object.sheet.is_owned_by(self.request.user)

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
            self.submissions = Submission.best \
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


class GroupMemberDeleteView(LoginRequiredMixin, SingleObjectMixin, generic.View):
    model = UserGroup
    slug_field = 'group_id'
    slug_url_kwarg = 'group_id'

    def post(self, request, *args, **kwargs):
        group = self.get_object()
        if group.author == request.user.profile:
            user = get_object_or_404(User, username=request.POST.get('member_username', ''))
            group.members.remove(user.profile)
        return redirect(self.request.META.get('HTTP_REFERER', reverse_lazy('home')))


class SheetTaskDeleteView(LoginRequiredMixin, SingleObjectMixin, generic.View):
    model = TaskSheet
    slug_field = 'sheet_id'
    slug_url_kwarg = 'sheet_id'

    def post(self, request, *args, **kwargs):
        sheet = self.get_object()
        if sheet.is_owned_by(request.user):
            task = get_object_or_404(Task,
                        task_id=request.POST.get('task_id', ''),
                        judge__judge_id=request.POST.get('judge_id', ''))
            sheet.tasks.remove(task)
        return redirect(self.request.META.get('HTTP_REFERER', reverse_lazy('home')))


class GroupMemberCreateView(LoginRequiredMixin, PassRequestMixin,
                            SuccessMessageMixin, generic.UpdateView):
    model = UserGroup
    slug_field = 'group_id'
    slug_url_kwarg = 'group_id'
    form_class = forms.GroupMemberCreateForm
    success_message = 'Success: Members were created.'
    template_name = 'info/group_add_members.html'

    def form_valid(self, form):
        group = self.get_object()
        if group.author == self.request.user.profile:
            users = []
            for username in map(str.strip, form.cleaned_data['usernames'].split(',')):
                for user in User.objects.filter(username=username):
                    users.append(user.profile)
            group.members.add(*users)
        return redirect('group-detail', group_id=group.group_id)


class AssignmentCreateView(LoginRequiredMixin, PassRequestMixin,
                           SuccessMessageMixin, generic.FormView):
    form_class = forms.AssignmentSheetCreateMultiForm
    template_name = 'info/assignment_create.html'
    assignment = None

    def form_valid(self, form):
        group = UserGroup.objects.get(group_id=self.kwargs['group_id'])
        sheet = form['sheet'].save()
        sheet = TaskSheet.objects.get(sheet_id=sheet.sheet_id)
        sheet.author = self.request.user.profile
        sheet.save()
        print(sheet, sheet.author, sheet.sheet_id)

        assignment = form['assignment'].save(commit=False)
        assignment.sheet = sheet
        assignment.group = group

        assignment.save()

        self.assignment = assignment
        return redirect('sheet-results',
                        group_id=self.assignment.group.group_id,
                        sheet_id=self.assignment.sheet.sheet_id)

class SheetCreateView(LoginRequiredMixin, PassRequestMixin, generic.FormView):
    model = TaskSheet
    form_class = forms.SheetCreateForm
    template_name = 'info/sheet_create.html'
    sheet = None

    def form_valid(self, form):
        sheet = form.save()
        sheet = TaskSheet.objects.get(sheet_id=sheet.sheet_id)
        sheet.author = self.request.user.profile
        sheet.save()
        self.sheet = sheet
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('sheet-detail', kwargs=dict(sheet_id=self.sheet.sheet_id))


class SheetTaskCreateView(LoginRequiredMixin, PassRequestMixin, SuccessMessageMixin, generic.FormView):
    form_class = forms.SheetTaskCreateForm
    success_message = 'Success: Task was added.'
    template_name = 'info/create_task.html'
    sheet = None

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse_lazy('home'))

    def form_valid(self, form):
        task, _ = Task.objects.get_or_create(
            judge=form.cleaned_data['judge'],
            task_id=form.cleaned_data['task_id'],
        )
        self.sheet.tasks.add(task)
        return super(SheetTaskCreateView, self).form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        sheet_id = kwargs['sheet_id']
        self.sheet = get_object_or_404(TaskSheet.objects, sheet_id=sheet_id)
        return super(SheetTaskCreateView, self).dispatch(request, *args, **kwargs)


class SheetDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = 'index.html'
    model = TaskSheet
    success_url = reverse_lazy('home')
    slug_url_kwarg = 'sheet_id'
    slug_field = 'sheet_id'

    def delete(self, request, *args, **kwargs):
        if self.get_object().is_owned_by(request.user):
            return super(SheetDeleteView, self).delete(request, *args, **kwargs)


class GroupDetailView(generic.DetailView):
    template_name = 'info/group_detail.html'
    model = UserGroup
    slug_url_kwarg = 'group_id'
    slug_field = 'group_id'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:
            kwargs['is_owner'] = self.request.user.profile == self.object.author
        kwargs['active_assignments'] = Assignment.active.filter(group=self.object)
        kwargs['future_assignments'] = Assignment.future.filter(group=self.object)
        return super(GroupDetailView, self).get_context_data(**kwargs)


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'info/dashboard_detail.html'
    model = UserProfile

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)

        context['groups_owned'] = UserGroup.objects.filter(author=self.request.user.profile).all()
        context['sheets'] = [{
            'sheet': sheet,
            'solved_count': Submission.best.filter(task__in=sheet.tasks.all(),
                author__user__user=self.request.user, verdict='AC').count()
        } for sheet in TaskSheet.objects.filter(author=self.request.user.profile).all()]
        context['assignations'] = [{
            'assignation': assignation,
            'solved_count': len(assignation.get_best_submissions().filter(
                author__user__user=self.request.user, verdict='AC').all()),
        } for assignation in Assignment.active.filter(group__in=self.request.user.profile.assigned_groups.all())]

        return context


class SheetDescriptionUpdateView(LoginRequiredMixin, PassRequestMixin, SuccessMessageMixin, generic.UpdateView):
    template_name = 'info/sheet_description_update.html'
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
        if self.object.is_owned_by(self.request.user):
            return super(SheetDescriptionUpdateView, self).form_valid(form)
