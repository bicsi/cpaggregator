from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.datetime_safe import datetime
from django.views import generic
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin

from accounts.forms import UserForm
from info.forms import UserUpdateForm, HandleCreateForm
from . import forms
from info.models import TaskSheet, Assignment
from data.models import UserProfile, UserHandle, UserGroup, Task, User, Submission

from info.tables import ResultsTable
from django_ajax.mixin import AJAXMixin


class ProfileUpdateView(LoginRequiredMixin, AJAXMixin, generic.UpdateView):
    template_name = 'info/modal/profile_update.html'
    success_message = 'Success: User was updated.'
    success_url = reverse_lazy('me')
    model = UserProfile
    form_class = UserUpdateForm
    slug_url_kwarg = 'username'
    slug_field = 'username'

    def get_object(self, queryset=None):
        return User.objects.get(username=self.kwargs['username']).profile

    def get_queryset(self):
        return super(ProfileUpdateView, self).get_queryset() \
            .filter(user=self.request.user)


class HandleCreateView(LoginRequiredMixin, AJAXMixin, generic.CreateView):
    template_name = 'info/modal/handle_create.html'
    success_message = 'Success: Handle was created.'
    model = UserHandle
    success_url = reverse_lazy('me')
    form_class = HandleCreateForm

    def get_form_kwargs(self):
        kwargs = super(HandleCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


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
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        return UserProfile.objects.get(user__username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        kwargs['is_owner'] = self.object.user == self.request.user
        return super(UserSubmissionsDetailView, self).get_context_data(**kwargs)


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


class GroupMemberAddView(LoginRequiredMixin, AJAXMixin, generic.UpdateView):
    model = UserGroup
    slug_field = 'group_id'
    slug_url_kwarg = 'group_id'
    form_class = forms.GroupMemberCreateForm
    template_name = 'info/modal/group_members_add.html'

    def form_valid(self, form):
        group = self.get_object()
        if group.author == self.request.user.profile:
            users = []
            for username in map(str.strip, form.cleaned_data['usernames'].split(',')):
                for user in User.objects.filter(username=username):
                    users.append(user.profile)
            group.members.add(*users)
        return redirect('group-detail', group_id=group.group_id)


class AssignmentCreateView(LoginRequiredMixin, AJAXMixin, generic.FormView):
    form_class = forms.AssignmentSheetCreateMultiForm
    template_name = 'info/modal/assignment_create.html'
    group = None

    def get_form_kwargs(self):
        kwargs = super(AssignmentCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        print(kwargs)
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(UserGroup, group_id=kwargs['group_id'])
        return super(AssignmentCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        print('GETTING CONTEXT DATA')
        context = super(AssignmentCreateView, self).get_context_data(**kwargs)
        context['object'] = self.group
        return context

    def form_valid(self, form):
        sheet = form['sheet'].save(commit=False)
        sheet.author = self.request.user.profile
        sheet.save()

        assignment = form['assignment'].save(commit=False)
        assignment.sheet = sheet
        assignment.group = self.group

        assignment.save()

        return redirect('sheet-results',
                        group_id=assignment.group.group_id,
                        sheet_id=assignment.sheet.sheet_id)


class GroupCreateView(LoginRequiredMixin, AJAXMixin, generic.FormView):
    model = UserGroup
    form_class = forms.GroupCreateForm
    template_name = 'info/modal/group_create.html'
    group = None

    def get_form_kwargs(self):
        kwargs = super(GroupCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.group = form.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('group-detail', kwargs=dict(group_id=self.group.group_id))


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
        return super(SheetTaskAddView, self).get_context_data(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(TaskSheet, sheet_id=self.kwargs['sheet_id'])
        return super(SheetTaskAddView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        task, _ = Task.objects.get_or_create(
            judge=form.cleaned_data['judge'],
            task_id=form.cleaned_data['task_id'],
        )
        self.object.tasks.add(task)
        return redirect(self.request.META.get('HTTP_REFERER', reverse_lazy('home')))


class SheetDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = 'index.html'
    model = TaskSheet
    success_url = reverse_lazy('home')
    slug_url_kwarg = 'sheet_id'
    slug_field = 'sheet_id'

    def delete(self, request, *args, **kwargs):
        if self.get_object().is_owned_by(request.user):
            return super(SheetDeleteView, self).delete(request, *args, **kwargs)


class TaskListView(LoginRequiredMixin, generic.ListView):
    template_name = 'info/task_list.html'
    paginate_by = 10
    context_object_name = 'task_list'
    model = Task
    ordering = ['name', 'task_id']

    def get_context_data(self, *args, **kwargs):
        kwargs['task_count'] = self.get_queryset().count()
        context = super(TaskListView, self).get_context_data(*args, **kwargs)
        task_list = context.pop('task_list')
        # Map task to verdict of current user.
        verdict_for_user_dict = {
            submission.task: submission.verdict for submission in
            Submission.best \
                .filter(author__user__user=self.request.user,
                        task__in=task_list)
        }
        context['task_list'] = [{
            'task': task,
            'verdict_for_user': verdict_for_user_dict.get(task),
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
        kwargs['best_submission_for_user'] = Submission.best.filter(
            task=task, author__user__user=self.request.user).first()
        kwargs['accepted_submissions'] = Submission.best.filter(
            task=task, verdict='AC')
        return super(TaskDetailView, self).get_context_data(**kwargs)


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


class GroupDeleteView(generic.DeleteView):
    slug_url_kwarg = 'group_id'
    slug_field = 'group_id'
    success_url = reverse_lazy('home')
    model = UserGroup

    def get_queryset(self):
        return super(GroupDeleteView, self).get_queryset() \
            .filter(author=self.request.user.profile)


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
        if self.object.is_owned_by(self.request.user):
            return super(SheetDescriptionUpdateView, self).form_valid(form)
        return redirect('home')
