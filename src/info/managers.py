from django.db import models
from django.utils import timezone


class AssignmentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(assigned_on__lte=timezone.now())

    def inactive(self):
        return self.filter(assigned_on__gt=timezone.now())