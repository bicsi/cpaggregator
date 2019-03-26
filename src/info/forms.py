from django import forms
from django.contrib.auth.models import User

from django.forms import SelectDateWidget

from data.models import UserProfile, UserHandle, Task, Judge, UserGroup
from info.models import TaskSheet, Assignment
from betterforms import multiform

from info.utils import slugify_unique


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class HandleCreateForm(forms.ModelForm):
    class Meta:
        model = UserHandle
        fields = ['judge', 'handle']

    def __init__(self, **kwargs):
        self.user = kwargs.pop('user')
        super(HandleCreateForm, self).__init__(**kwargs)

    def save(self, commit=True):
        handle = super(HandleCreateForm, self).save(commit=False)
        handle.user = self.user.profile
        if commit:
            handle.save()
        return handle


class GroupMemberCreateForm(forms.Form):
    usernames = forms.CharField(label='Usernames (separated by comma)', max_length=2048)

    def __init__(self, *args, **kwargs):
        kwargs.pop('instance')
        super(GroupMemberCreateForm, self).__init__(*args, **kwargs)


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']


class SheetTaskCreateForm(forms.Form):
    judge = forms.ModelChoiceField(queryset=Judge.objects)
    task_id = forms.CharField(
        label='Task id',
        help_text='Example: binar (infoarena), 505_E (codeforces), 0-k-multiple (csacademy)',
        max_length=256)


class SheetDescriptionUpdateForm(forms.ModelForm):
    class Meta:
        fields = ['title', 'description']
        model = TaskSheet
        help_texts = {
            'description': 'You can write your description using Markdown.',
        }


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = UserGroup
        fields = ['name', 'visibility']
        help_texts = {
            'name': 'Choose a name for the group.',
            'visibility': 'You can always change the visibility in the future.',
        }

    def __init__(self, **kwargs):
        self.user = kwargs.pop('user')
        super(GroupCreateForm, self).__init__(**kwargs)

    def save(self, commit=True):
        group = super(GroupCreateForm, self).save(commit=False)
        group.group_id = slugify_unique(UserGroup, group.name, 'group_id')
        group.author = self.user.profile
        if commit:
            group.save()
        return group


class SheetCreateForm(forms.ModelForm):
    class Meta:
        model = TaskSheet
        fields = ['title']
        help_texts = {
            'title': "Example: \"Dynamic Programming super-tasks\"."
        }
    def __init__(self, **kwargs):
        print(kwargs)
        self.user = kwargs.pop('user')
        super(SheetCreateForm, self).__init__(**kwargs)

    def save(self, commit=True):
        sheet = super(SheetCreateForm, self).save(commit=False)
        sheet.sheet_id = slugify_unique(TaskSheet, sheet.title, 'sheet_id')
        sheet.author = self.user.profile
        if commit:
            sheet.save()
        return sheet


class AssignmentCreateForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['assigned_on', 'use_best_recent']
        widgets = {
            'assigned_on': SelectDateWidget(),
        }

    def __init__(self, **kwargs):
        user = kwargs.pop('user')
        super(AssignmentCreateForm, self).__init__(**kwargs)


class AssignmentSheetCreateMultiForm(multiform.MultiModelForm):
    form_classes = {
        'sheet': SheetCreateForm,
        'assignment': AssignmentCreateForm,
    }


class GroupUpdateForm(forms.ModelForm):
    class Meta:
        fields = ['name', 'visibility', 'description']
        model = UserGroup
        help_texts = {
            'description': 'You can write your description using Markdown.',
        }