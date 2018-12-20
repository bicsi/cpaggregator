from django.shortcuts import render

# Create your views here.
from django.urls import reverse_lazy
from django.views import generic

from contact import forms
from contact.models import FeedbackMessage


class FeedbackCreateView(generic.CreateView):
    template_name = 'contact/feedback_create.html'
    model = FeedbackMessage
    form_class = forms.FeedbackCreateForm
    success_url = reverse_lazy('home')

    def get_form_kwargs(self):
        kwargs = super(FeedbackCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
