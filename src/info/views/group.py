import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django_ajax.mixin import AJAXMixin
from rest_framework.response import Response
from rest_framework.views import APIView

from data.models import UserGroup, Submission, GroupMember
from info import forms, queries
from info.models import Assignment
from info.utils import compute_asd_scores, build_group_card_context


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
        self.group = get_object_or_404(
            UserGroup,
            group_id=kwargs['group_id'],
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
            for profile in users:
                GroupMember.objects.get_or_create(group=group, profile=profile)

        return redirect('group-detail', group_id=group.group_id)


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


class GroupMemberRoleChange(LoginRequiredMixin, SingleObjectMixin, generic.View):
    model = GroupMember

    def get_object(self, queryset=None):
        return get_object_or_404(GroupMember, group__group_id=self.kwargs['group_id'],
                                 profile__user__username=self.request.POST.get('username'))

    def post(self, request, *args, **kwargs):
        group_member = self.get_object()
        if group_member.group.is_owned_by(request.user):
            role = request.POST.get('role')
            group_member.role = role
            group_member.save()
        return redirect(self.request.META.get('HTTP_REFERER', reverse_lazy('home')))


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


class GroupDetailView(generic.DetailView):
    template_name = 'info/group_detail.html'
    model = UserGroup
    slug_url_kwarg = 'group_id'
    slug_field = 'group_id'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        group = self.object

        assignments = Assignment.objects.active().filter(group=group)
        if self.request.user.is_authenticated:
            is_owner = group.is_owned_by(self.request.user)
            if is_owner:
                assignments = Assignment.objects.filter(group=group)

            kwargs['is_owner'] = is_owner
            kwargs['is_user_member'] = self.request.user.profile.assigned_groups.filter(id=group.id).exists()
            kwargs['judges'] = queries.get_all_judges(group)
            kwargs['assignments'] = [{
                'assignment': assignment,
                'solved_count': Submission.objects.best().filter(
                    author__in=self.request.user.profile.handles.all(),
                    task__in=assignment.sheet.tasks.all(),
                    verdict='AC').count()
            } for assignment in assignments.all()]
        else:
            kwargs['assignments'] = [{'assignment': assignment} for assignment in assignments.all()]

        members = GroupMember.objects.filter(group=group).select_related('profile').all()

        kwargs['members'] = [{
            'member': member.profile,
            'role': member.role,
        } for member in members]

        # if group.group_id == 'asd-seminar' and 0:
        #     scores = compute_asd_scores(group)
        #
        #         'scores': scores[member.profile.id],
        #     } for member in members]
        #     kwargs['max_score'] = 10

        return super(GroupDetailView, self).get_context_data(**kwargs)


class GroupDeleteView(generic.DeleteView):
    slug_url_kwarg = 'group_id'
    slug_field = 'group_id'
    success_url = reverse_lazy('home')
    model = UserGroup

    def get_queryset(self):
        return super(GroupDeleteView, self).get_queryset() \
            .filter(author=self.request.user.profile)


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


class GroupListView(LoginRequiredMixin, generic.ListView):
    template_name = 'info/group_list.html'
    paginate_by = 15
    context_object_name = 'group_list'

    def get_queryset(self):
        return UserGroup.public.annotate(
            member_count=Count('members')).order_by('-member_count')

    def get_context_data(self, *args, **kwargs):
        kwargs['group_count'] = self.get_queryset().count()
        context = super(GroupListView, self).get_context_data(*args, **kwargs)
        group_list = context.pop('group_list')
        context['group_list'] = build_group_card_context(self.request, group_list)
        return context


class GroupAssignmentOrderingUpdate(APIView):
    def post(self, request, *args, **kwargs):
        group_id = kwargs['group_id']
        ordering = json.loads(request.data.get('ordering'))
        ordering_index = {int(elem): int(idx) for idx, elem in enumerate(ordering)}
        print(ordering_index)

        group = get_object_or_404(UserGroup, group_id=group_id)
        if group.is_owned_by(request.user):
            for idx, assignment in enumerate(Assignment.objects.filter(group=group).all()):
                assignment.ordering_id = ordering_index.get(idx)
                assignment.save()
            return Response({'success': 'Success'})