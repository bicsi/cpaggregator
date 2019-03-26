from django.db import models
from django.db.models import Case, Value, When, IntegerField, F


class BestSubmissionManager(models.Manager):
    def get_queryset(self):
        best_submissions = super(BestSubmissionManager, self).get_queryset() \
            .annotate(is_ac=Case(
                When(verdict='AC', then=Value(1)),
                default=Value(0),
                output_field=IntegerField())) \
            .order_by('author', 'task', '-is_ac',
                      F('score').desc(nulls_last=True), 'submitted_on') \
            .distinct('author', 'task')
        # This is to fix multiple order by's and such.
        return super(BestSubmissionManager, self).get_queryset().filter(id__in=best_submissions)


class BestRecentSubmissionManager(models.Manager):
    def get_queryset(self):
        best_submissions = super(BestRecentSubmissionManager, self).get_queryset() \
            .annotate(is_ac=Case(
                When(verdict='AC', then=Value(1)),
                default=Value(0),
                output_field=IntegerField())) \
            .order_by('author', 'task', '-is_ac',
                      F('score').desc(nulls_last=True), '-submitted_on') \
            .distinct('author', 'task')
        # This is to fix multiple order by's and such.
        return super(BestRecentSubmissionManager, self).get_queryset().filter(id__in=best_submissions)


class JudgeManager(models.Manager):
    def get_queryset(self):
        return super(JudgeManager, self).get_queryset() \
            .filter(judge_id__in=['csa', 'cf', 'ia', 'ojuz', 'ac'])


class PublicGroupManager(models.Manager):
    def get_queryset(self):
        return super(PublicGroupManager, self).get_queryset() \
            .filter(visibility='PUBLIC')