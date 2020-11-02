from django.db import models
from data.models import UserProfile, Task


class ProfileScheduleInfo(models.Model):
    profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE,
        related_name='schedule_info')
    last_updated_on = models.DateField(null=True, blank=True)


class TaskScheduleInfo(models.Model):
    task = models.OneToOneField(
        Task, on_delete=models.CASCADE,
        related_name='schedule_info')
    last_updated_on = models.DateField(null=True, blank=True)
