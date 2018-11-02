from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from accounts.models import UserProfileClaim
from data.models import UserProfile
from . import forms


class LoginView(generic.FormView):
    form_class = AuthenticationForm
    success_url = reverse_lazy("home")
    template_name = "accounts/login.html"

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request, **self.get_form_kwargs())

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)


class RegisterView(generic.CreateView):
    form_class = forms.RegisterForm
    success_url = reverse_lazy("login")
    template_name = "accounts/register.html"


class LogoutView(generic.RedirectView):
    url = reverse_lazy("home")

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class ClaimCreate(generic.RedirectView, LoginRequiredMixin):
    def get(self, request, *args, **kwargs):
        profile = get_object_or_404(UserProfile, username=kwargs['username'])
        UserProfileClaim.objects.create(
            user=request.user,
            profile=profile,
        )
        return redirect('home')
