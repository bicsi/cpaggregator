from django.db import models
from data.models import UserProfile, Task


class ProfileScheduleInfo(models.Model):
    profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE,
        related_name='schedule_info')
    last_updated_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.profile} [updated on {self.last_updated_on}]"


class TaskScheduleInfo(models.Model):
    task = models.OneToOneField(
        Task, on_delete=models.CASCADE,
        related_name='schedule_info')
    last_updated_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.task} [updated on {self.last_updated_on}]"
