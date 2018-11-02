from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from accounts.forms import UserForm
from info.forms import UserProfileUpdateForm
from info.models import TaskSheet
from data.models import UserProfile, UserHandle

from info.tables import ResultsTable
from django.contrib.messages.views import SuccessMessageMixin
from bootstrap_modal_forms.mixins import PassRequestMixin


class ProfileUpdateView(LoginRequiredMixin, PassRequestMixin,
                        SuccessMessageMixin, generic.UpdateView):
    template_name = 'info/update_profile.html'
    form_class = UserProfileUpdateForm
    success_message = 'Success: User was updates.'
    success_url = reverse_lazy('me')
    model = UserProfile
    slug_url_kwarg = 'username'
    slug_field = 'username'

    def get_queryset(self):
        return super(ProfileUpdateView, self).get_queryset() \
            .filter(user=self.request.user)


class MeDetailView(LoginRequiredMixin, generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy('profile', kwargs={
            'username': self.request.user.profile.username})


class UserSubmissionsDetailView(generic.DetailView):
    template_name = 'info/user_submissions_detail.html'
    model = UserProfile
    slug_url_kwarg = 'username'
    slug_field = 'username'


class ResultsDetailView(generic.DetailView):
    template_name = 'info/results_detail.html'
    model = TaskSheet
    slug_url_kwarg = 'sheet_id'
    slug_field = 'sheet_id'
    table = None

    def get_object(self, **kwargs):
        obj = super().get_object(**kwargs)
        submissions = obj.get_best_submissions()
        self.table = ResultsTable(submissions)
        print(submissions)
        return obj

    def get_context_data(self, **kwargs):
        print(kwargs)
        kwargs['table'] = self.table
        return super().get_context_data(**kwargs)


class DashboardView(generic.TemplateView):
    template_name = 'info/dashboard_detail.html'
    model = UserProfile
