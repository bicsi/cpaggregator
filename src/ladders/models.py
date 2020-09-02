from django.db import models

# Create your models here.
from django.db.models import F
from django.utils import timezone

from data.models import UserProfile, Task, Judge
from django.utils.translation import gettext_lazy as _


class Ladder(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.profile}"


class LadderTask(models.Model):
    class Status(models.TextChoices):
        RUNNING = 'RUN', _('In Progress')
        EXPIRED = 'EXP', _('Expired')
        COMPLETED = 'COM', _('Completed')
        NEW = 'NEW', _('New')
        LOCKED = 'LOC', _('Locked')

    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    ladder = models.ForeignKey(Ladder, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(choices=Status.choices, max_length=3)
    started_on = models.DateTimeField(null=True)
    duration = models.DurationField()

    @property
    def remaining_time(self):
        if self.status != LadderTask.Status.RUNNING:
            return None
        return self.started_on + self.duration - timezone.now()

    @property
    def is_finished(self):
        return self.status in [
            LadderTask.Status.EXPIRED,
            LadderTask.Status.COMPLETED,
        ]

    def start(self):
        if self.status != LadderTask.Status.NEW:
            raise ValueError("Status is not new.")
        self.started_on = timezone.now()
        self.status = LadderTask.Status.RUNNING
        self.save()

    class Meta:
        ordering = [F('started_on').asc(nulls_last=True)]

    def __str__(self):
        return f"{self.ladder}: {self.task} ({self.status})"



