import datetime

from betterforms import multiform
from bootstrap_datepicker_plus import DateTimePickerInput
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from data.models import UserProfile, UserHandle, Judge, UserGroup, TaskStatement
from info.models import TaskSheet, Assignment, CustomTaskTag, TaskSheetTask
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
    task_url = forms.CharField(
        label='Task URL',
        help_text='Example: "http://codeforces.com/gym/102419/problem/A", "infoarena.ro/problema/adunare"'
    )


class SheetTaskEditForm(forms.ModelForm):
    task_url = forms.CharField(
        label="Task URL",
        disabled=True,
        help_text='You cannot change the task URL once it\'s added')

    class Meta:
        model = TaskSheetTask
        fields = ['score']


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


FORMAT = '%d.%m.%Y %H:%M'


def get_date_time_picker_widget(required=True):
    return DateTimePickerInput(
        format=FORMAT,
        options=dict(
            showClose=False,
            showClear=not required,
            showTodayButton=True))


class AssignmentCreateForm(forms.ModelForm):
    assigned_on = forms.DateTimeField(
        input_formats=[FORMAT],
        widget=get_date_time_picker_widget(),
        initial=timezone.now(),
        help_text='When the assignment will start showing up. Time is in UTC+0.')

    end_on = forms.DateTimeField(
        input_formats=[FORMAT],
        widget=get_date_time_picker_widget(required=False),
        required=False,
        help_text='Optional. When the assignment will end. Time is in UTC+0.')

    class Meta:
        model = Assignment
        fields = ['assigned_on', 'use_best_recent', 'end_on']

    def __init__(self, **kwargs):
        kwargs.pop('user')
        super(AssignmentCreateForm, self).__init__(**kwargs)


class AssignmentUpdateForm(forms.ModelForm):

    assigned_on = forms.DateTimeField(
        input_formats=[FORMAT],
        widget=get_date_time_picker_widget(),
        help_text='When the assignment will start showing up. Time is in UTC+0.')

    end_on = forms.DateTimeField(
        input_formats=[FORMAT],
        widget=get_date_time_picker_widget(required=False),
        required=False,
        help_text='Optional. When the assignment will end. Time is in UTC+0.')

    class Meta:
        model = Assignment
        fields = ['assigned_on', 'end_on',
                  'use_best_recent',
                  'hide_submissions_before_assigned']


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


class TaskCustomTagCreateForm(forms.ModelForm):
    class Meta:
        model = CustomTaskTag
        fields = ['name']


class TaskStatementUpdateForm(forms.ModelForm):
    class Meta:
        model = TaskStatement
        fields = ['text', 'examples']
        help_texts = {
            'text': 'Text is Markdown. Support for LaTeX is done via `$ LATEX TEXT $`.',
        }

    def save(self, commit=True):
        obj = super(TaskStatementUpdateForm, self).save(commit=False)
        obj.modified_by_user = True
        if commit:
            obj.save()
        return obj
