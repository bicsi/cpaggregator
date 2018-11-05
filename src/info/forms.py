from django import forms
from django.contrib.auth.models import User

from bootstrap_modal_forms.mixins import PopRequestMixin, CreateUpdateAjaxMixin

from data.models import UserProfile, UserHandle


class UserUpdateForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class HandleCreateForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.ModelForm):
    class Meta:
        model = UserHandle
        fields = ['judge', 'handle']

    def save(self, *args, **kwargs):
        kwargs['commit'] = False
        obj = super(HandleCreateForm, self).save(*args, **kwargs)
        if self.request:
            obj.user = self.request.user.profile
        obj.save()
        return obj


class ProfileUpdateForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']