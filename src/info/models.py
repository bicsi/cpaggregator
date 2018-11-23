from django.db import models
from django.db.models import F, Manager, Case, When, Value, IntegerField
from django.utils import timezone
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify

from data.models import UserGroup, Submission, Task, UserProfile


class TaskSheet(models.Model):
    title = models.CharField(max_length=256, default="Results")
    sheet_id = models.CharField(max_length=256, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    description = MarkdownxField(blank=True, null=True)
    tasks = models.ManyToManyField(Task)
    is_public = models.BooleanField(default=False)
    author = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.CASCADE)

    @property
    def formatted_description(self):
        return markdownify(self.description)

    def is_owned_by(self, user):
        return user.is_superuser or user.profile == self.author

    def __str__(self):
        return self.title


class Assignment(models.Model):
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    sheet = models.ForeignKey(TaskSheet, on_delete=models.CASCADE)
    assigned_on = models.DateTimeField()

    def get_all_users(self):
        return self.group.members.all()

    def get_all_submissions(self):
        return Submission.objects.filter(
            author__user__in=self.get_all_users(),
            task__in=self.sheet.tasks.all(),
        ).order_by('submitted_on')

    def get_best_submissions(self):
        return Submission.best.filter(
            author__user__in=self.get_all_users(),
            task__in=self.sheet.tasks.all(),
        ).order_by('submitted_on')

    class Meta:
        unique_together = (('group', 'sheet'),)




