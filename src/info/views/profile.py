from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy

from data.models import UserProfile, UserHandle, Submission
from django_ajax.mixin import AJAXMixin

from info.forms import UserUpdateForm, HandleCreateForm
from django.views import generic

import json


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
        kwargs['solved_tasks'], kwargs['unsolved_tasks'] = [], []
        best_submissions = Submission.objects.best().filter(author__user=self.object).select_related('task')
        for submission in best_submissions.all():
            task_data = {
                'submission': submission,
                'task': submission.task,
            }
            if submission.verdict == 'AC':
                kwargs['solved_tasks'].append(task_data)
            else:
                kwargs['unsolved_tasks'].append(task_data)
        try:
            statistics = self.object.statistics
            if statistics.activity:
                activity = json.loads(statistics.activity)
                kwargs['activity'] = {
                    'timestamps': json.dumps([activity_point['name']
                                              for activity_point in activity]),
                    'ac_submission_count': json.dumps([activity_point['ac_submission_count']
                                                       for activity_point in activity]),
                    'total_submission_count': json.dumps([activity_point['total_submission_count']
                                                          for activity_point in activity]),
                }
            if statistics.tag_stats:
                tag_data = sorted(json.loads(statistics.tag_stats), key=lambda x: x['solved_count'], reverse=True)[:8]
                kwargs['tag_data'] = {
                    'tags': json.dumps([tag_data_point['tag'] for tag_data_point in tag_data]),
                    'solved_count': json.dumps([tag_data_point['solved_count'] for tag_data_point in tag_data]),
                }
        except UserProfile.statistics.RelatedObjectDoesNotExist:
            pass
        return super(UserSubmissionsDetailView, self).get_context_data(**kwargs)
