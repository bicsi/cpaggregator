from django.db import models
from django.db.models import Case, Value, When, IntegerField, F
from django.utils import timezone


class ActiveAssignmentManager(models.Manager):
    def get_queryset(self):
        return super(ActiveAssignmentManager, self).get_queryset() \
            .filter(assigned_on__lte=timezone.now())


class FutureAssignmentManager(models.Manager):
    def get_queryset(self):
        return super(FutureAssignmentManager, self).get_queryset() \
            .filter(assigned_on__gt=timezone.now())
