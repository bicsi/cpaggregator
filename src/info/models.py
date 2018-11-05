
from django.db import models
from django.db.models import F, Manager, Case, When, Value, IntegerField
from django.utils import timezone

import data.models as data_models


class TaskSheet(models.Model):
    title = models.CharField(max_length=256, default="Results")
    sheet_id = models.CharField(max_length=256, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    users = models.ManyToManyField(data_models.UserProfile, blank=True, related_name='assigned_sheets')
    groups = models.ManyToManyField(data_models.UserGroup, blank=True, related_name='assigned_sheets')
    tasks = models.ManyToManyField(data_models.Task)

    def get_all_users(self):
        result = list(self.users.all())
        for group in self.groups.all():
            result += list(group.members.all())
        return set(result)

    def get_all_submissions(self):
        return data_models.Submission.objects.filter(
            author__user__in=self.get_all_users(),
            task__in=self.tasks.all(),
        )

    def get_best_submissions(self):
        best_submissions = self.get_all_submissions() \
            .annotate(is_ac=Case(
                When(verdict='AC', then=Value(1)),
                default=Value(0),
                output_field=IntegerField())) \
            .order_by('author', 'task', '-is_ac', F('score').desc(nulls_last=True), 'submitted_on') \
            .distinct('author', 'task')

        return data_models.Submission.objects \
            .filter(id__in=best_submissions) \
            .order_by('submitted_on')

    def __str__(self):
        return self.title




