from django.db import models
from django.utils import timezone


class AssignmentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(assigned_on__lte=timezone.now()) \
                   .exclude(end_on__lt=timezone.now())

    def visible(self):
        return self.filter(assigned_on__lte=timezone.now())
