from django import forms

from contact.models import FeedbackMessage


class FeedbackCreateForm(forms.ModelForm):
    class Meta:
        model = FeedbackMessage
        fields = ['title', 'content']

    def __init__(self, **kwargs):
        self.user = kwargs.pop('user')
        super(FeedbackCreateForm, self).__init__(**kwargs)

    def save(self, commit=True):
        feedback = super(FeedbackCreateForm, self).save(commit=False)
        feedback.author = self.user.profile
        if commit:
            feedback.save()
        return feedback
