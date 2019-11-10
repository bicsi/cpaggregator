from django.db import models
from django.db.models import Case, Value, When, IntegerField, F


class SubmissionQuerySet(models.QuerySet):
    def best(self, use_recent=False):
        best_submissions = self.annotate(is_ac=Case(
            When(verdict='AC', then=Value(1)),
            default=Value(0),
            output_field=IntegerField())) \
            .order_by('author', 'task', '-is_ac',
                      F('score').desc(nulls_last=True),
                      f"{'-' if use_recent else ''}submitted_on") \
            .distinct('author', 'task')
        # This is to fix multiple order by's and such.
        return self.filter(id__in=best_submissions)

    def accepted(self):
        return self.filter(verdict='AC')


class JudgeManager(models.Manager):
    def get_queryset(self):
        return super(JudgeManager, self).get_queryset() \
            .filter(judge_id__in=['csa', 'cf', 'ia', 'ojuz', 'ac'])


class PublicGroupManager(models.Manager):
    def get_queryset(self):
        return super(PublicGroupManager, self).get_queryset() \
            .filter(visibility='PUBLIC')
