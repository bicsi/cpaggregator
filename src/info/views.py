from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.datetime_safe import datetime
from django.views import generic
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
import json

from accounts.forms import UserForm
from info.forms import UserUpdateForm, HandleCreateForm
from . import forms
from info.models import TaskSheet, Assignment, FavoriteTask, TaskSheetTask
from data.models import UserProfile, UserHandle, UserGroup, Task, User, Submission

from info.tables import ResultsTable
from django_ajax.mixin import AJAXMixin
from rest_framework.views import APIView
from rest_framework.response import Response

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
        statistics = self.object.statistics
        if statistics.activity:
            kwargs['activity'] = statistics.activity
        if statistics.tag_stats:
            tag_data = sorted(json.loads(statistics.tag_stats), key=lambda x: x['solved_count'], reverse=True)[:5]
            kwargs['tag_data'] = json.dumps(tag_data)

        return super(UserSubmissionsDetailView, self).get_context_data(**kwargs)


class ResultsDetailView(generic.DetailView):
    template_name = 'info/results_detail.html'
    model = Assignment
    table = None
    submissions = None
    show_results = None
    show_submissions = None
    context_object_name = 'assignment'

    def get_object(self, **kwargs):
        obj = Assignment.objects.get(group__group_id=self.kwargs['group_id'],
                                     sheet__sheet_id=self.kwargs['sheet_id'])
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
        tasks = [{'task': task.task, 'verdict_for_user': verdict_for_user_dict.get(task.task)}
                 for task in TaskSheetTask.objects.filter(sheet=self.object.sheet).all()]

        # Send results data.
        results_data = []
        for user in self.object.group.members.all():
            user_submissions = []
            found_one_submission = False
            for task in tasks:
                submission = self.object.get_best_submissions() \
                    .filter(author__user=user, task=task['task'])
                if submission.exists():
                    user_submissions.append(submission.first())
                    found_one_submission = True
                else:
                    user_submissions.append(None)
            if found_one_submission:
                results_data.append({
                    'user': user,
                    'results': user_submissions,
                })

        context['tasks'] = tasks
        context['is_owner'] = self.object.sheet.is_owned_by(self.request.user)
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
        if group.is_owned_by(request.user):
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
            task = get_object_or_404(TaskSheetTask,
                        sheet=sheet,
                        task__task_id=request.POST.get('task_id', ''),
                        task__judge__judge_id=request.POST.get('judge_id', ''))
            task.delete()
        return redirect(self.request.META.get('HTTP_REFERER', reverse_lazy('home')))


class GroupMemberAddView(LoginRequiredMixin, AJAXMixin, generic.UpdateView):
    model = UserGroup
    slug_field = 'group_id'
    slug_url_kwarg = 'group_id'
    form_class = forms.GroupMemberCreateForm
    template_name = 'info/modal/group_members_add.html'

    def form_valid(self, form):
        group = self.get_object()
        if group.is_owned_by(self.request.user):
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
        self.group = get_object_or_404(UserGroup, group_id=kwargs['group_id'],
                                       author=self.request.user.profile)
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

        return redirect('group-sheet-detail',
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
            task_id=form.cleaned_data['task_id'].lower(),
        )
        TaskSheetTask.objects.create(
            task=task,
            sheet=self.object,
        )
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
    queryset = Task.objects.order_by(
        F('statistics__difficulty_score').asc(nulls_last=True))

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
        favorite_tasks = {favorite.task for favorite in
                          self.request.user.profile.favorite_tasks.all()}
        context['task_list'] = [{
            'task': task,
            'verdict_for_user': verdict_for_user_dict.get(task),
            'faved': task in favorite_tasks,
        } for task in task_list]
        return context


class RankListView(generic.ListView):
    template_name = 'info/rank_list.html'
    paginate_by = 10
    context_object_name = 'profile_list'
    queryset = UserProfile.objects.order_by('statistics__rank')

    def get_context_data(self, **kwargs):
        kwargs['user_count'] = UserProfile.objects.count()
        return super(RankListView, self).get_context_data(**kwargs)


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
        kwargs['user_has_handle'] = UserHandle.objects.filter(
            judge=task.judge, user=self.request.user.profile
        ).exists()
        kwargs['is_favorited'] = self.request.user.profile.favorite_tasks.filter(
            task=task).exists()
        return super(TaskDetailView, self).get_context_data(**kwargs)


class GroupDetailView(generic.DetailView):
    template_name = 'info/group_detail.html'
    model = UserGroup
    slug_url_kwarg = 'group_id'
    slug_field = 'group_id'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        assignments = list(Assignment.active.filter(group=self.object).order_by('-assigned_on').all())
        if self.request.user.is_authenticated:
            is_owner = self.object.is_owned_by(self.request.user)
            if is_owner:
                assignments = list(Assignment.future.filter(group=self.object).order_by('-assigned_on').all()) \
                                        + assignments
            kwargs['is_owner'] = is_owner
            kwargs['is_user_member'] = self.request.user.profile.assigned_groups.filter(id=self.object.id).exists()

            kwargs['assignments'] = [{
                'assignment': assignment,
                'solved_count': Submission.best.filter(
                    author__in=self.request.user.profile.handles.all(),
                    task__in=assignment.sheet.tasks.all(),
                    verdict='AC').count()
            } for assignment in assignments]
        else:
            kwargs['assignments'] = [{'assignment': assignment} for assignment in assignments]

        members = self.object.members.all()
        scores = {member.id: [] for member in members}
        bonuses = {member.id: 0 for member in members}
        non_bonuses = {member.id: 0 for member in members}

        if self.object.group_id == 'asd-seminar':
            for assignment in self.object.assignment_set.all():
                submissions = Submission.best.filter(
                    author__user__in=members,
                    task__in=assignment.sheet.tasks.all(),
                    submitted_on__gte=assignment.assigned_on,
                    verdict='AC',
                ).order_by('submitted_on').all()

                bonus_given = {}
                for submission in submissions:
                    bonus = bonus_given.get(submission.task.id, 0)
                    if bonus < 7 and bonuses[submission.author.user.id] < 7:
                        bonuses[submission.author.user.id] += 1
                        bonus_given[submission.task.id] = bonus + 1
                        scores[submission.author.user.id].append({
                            'submission': submission,
                            'bonus': True,
                        })
                    elif non_bonuses[submission.author.user.id] < 3:
                        non_bonuses[submission.author.user.id] += 1
                        scores[submission.author.user.id].append({
                            'submission': submission,
                            'bonus': False,
                        })
            kwargs['members'] = [{'member': member, 'scores': scores[member.id]} for member in members]
            kwargs['max_score'] = 10
        else:
            kwargs['members'] = [{'member': member} for member in members]

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

        task_list = Task.objects.order_by('-created_at')[:5]

        # Map task to verdict of current user.
        verdict_for_user_dict = {
            submission.task: submission.verdict for submission in
            Submission.best \
                .filter(author__user__user=self.request.user,
                        task__in=task_list)
        }
        favorite_tasks = {favorite.task for favorite in
                          self.request.user.profile.favorite_tasks.all()}
        context['newly_added_task_list'] = [{
            'task': task,
            'verdict_for_user': verdict_for_user_dict.get(task),
            'faved': task in favorite_tasks,
        } for task in task_list]

        context['public_groups_data'] = [{
            "group": group,
            "assignments": [{
                "assignment": assignment,
                "task_count": assignment.sheet.tasks.count(),
            } for assignment in Assignment.active.filter(group=group).order_by('-assigned_on')[:3]],
            "assignment_count": Assignment.active.filter(group=group).count(),
        } for group in UserGroup.public.all()]

        context['owned_groups_data'] = [{
            "group": group,
            "assignments": [{
                "assignment": assignment,
                "task_count": assignment.sheet.tasks.count(),
            } for assignment in Assignment.objects.filter(group=group).order_by('-assigned_on')[:3]],
            "assignment_count": Assignment.objects.filter(group=group).count(),
        } for group in self.request.user.profile.owned_groups.all()]

        context['assigned_groups_data'] = [{
            "group": group,
            "assignments": [{
                "assignment": assignment,
                "solved_count": assignment.get_best_submissions().filter(
                    author__user__user=self.request.user, verdict='AC').count(),
                "task_count": assignment.sheet.tasks.count(),
            } for assignment in Assignment.active.filter(group=group).order_by('-assigned_on')[:3]],
            "assignment_count": Assignment.active.filter(group=group).count(),
        } for group in self.request.user.profile.assigned_groups.all()]


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


class GroupJoinView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        user = request.user
        group = get_object_or_404(
            UserGroup,
            group_id=self.kwargs['group_id'],
            visibility='PUBLIC')
        group.members.add(user.profile)
        group.save()
        return redirect('group-detail', group_id=group.group_id)


class GroupLeaveView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        user = request.user
        group = get_object_or_404(UserGroup, group_id=self.kwargs['group_id'])
        group.members.remove(user.profile)
        group.save()

        return redirect('group-detail', group_id=group.group_id)


class GroupUpdateView(LoginRequiredMixin, AJAXMixin, generic.UpdateView):
    template_name = 'info/modal/group_update.html'
    model = UserGroup
    slug_url_kwarg = 'group_id'
    slug_field = 'group_id'
    form_class = forms.GroupUpdateForm

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', reverse_lazy('home'))

    def form_valid(self, form):
        if self.object.is_owned_by(self.request.user):
            return super(GroupUpdateView, self).form_valid(form)
        return redirect('home')


class UpdateSheetTaskOrdering(APIView):

    def post(self, request, *args, **kwargs):
        print('POST')
        sheet_id = kwargs['sheet_id']
        print(request.data)
        ordering = json.loads(request.data.get('ordering'))
        ordering_index = {int(elem): int(idx) for idx, elem in enumerate(ordering)}

        print(ordering)
        sheet = get_object_or_404(TaskSheet, sheet_id=sheet_id)
        if sheet.is_owned_by(request.user):
            for idx, task in enumerate(TaskSheetTask.objects.filter(sheet=sheet).all()):
                print(f'{task} -> {ordering_index.get(idx)}')
                task.ordering_id = ordering_index.get(idx)
                task.save()
            return Response({'success': 'Success'})
