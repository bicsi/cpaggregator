from django import forms
from django.contrib.auth.models import User

from bootstrap_modal_forms.mixins import PopRequestMixin, CreateUpdateAjaxMixin
from django.forms import SelectDateWidget

from data.models import UserProfile, UserHandle, Task, Judge
from info.models import TaskSheet, Assignment
from betterforms import multiform


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


class GroupMemberCreateForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.Form):
    usernames = forms.CharField(label='Usernames (separated by comma)', max_length=256)

    def __init__(self, *args, **kwargs):
        kwargs.pop('instance')
        super(GroupMemberCreateForm, self).__init__(*args, **kwargs)


class ProfileUpdateForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']


class SheetTaskCreateForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.Form):
    judge = forms.ModelChoiceField(queryset=Judge.objects)
    task_id = forms.CharField(
        label='Task id',
        help_text='Example: binar (infoarena), 505_E (codeforces), 0-k-multiple (csacademy)',
        max_length=256)


class SheetDescriptionUpdateForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.ModelForm):
    class Meta:
        fields = ['title', 'description']
        model = TaskSheet
        help_texts = {
            'description': 'You can write your description using Markdown.',
        }


class SheetCreateForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.ModelForm):
    class Meta:
        model = TaskSheet
        fields = ['title', 'sheet_id']


class AssignmentCreateForm(PopRequestMixin, CreateUpdateAjaxMixin, forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['assigned_on']
        widgets = {
            'assigned_on': SelectDateWidget(),
        }


class AssignmentSheetCreateMultiForm(multiform.MultiModelForm):
    form_classes = {
        'sheet': SheetCreateForm,
        'assignment': AssignmentCreateForm,
    }