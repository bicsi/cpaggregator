from django.db import models
import math
from data.models import Task, UserProfile, Submission
from django.contrib.postgres.fields import JSONField

from ladders.models import Ladder


class TaskStatistics(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='statistics')
    users_tried_count = models.IntegerField(default=0)
    users_solved_count = models.IntegerField(default=0)
    submission_count = models.IntegerField(default=0)
    favorited_count = models.IntegerField(default=0)
    difficulty_score = models.IntegerField(default=1)

    @property
    def mean_submission_count(self):
        if self.users_solved_count == 0:
            return math.nan
        return self.submission_count / self.users_tried_count

    @property
    def acceptance_rate(self):
        if self.users_solved_count == 0:
            return math.nan
        return 100 * self.users_solved_count / self.users_tried_count


class UserStatistics(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='statistics')
    tasks_solved_count = models.IntegerField(default=0)
    tasks_tried_count = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    rank = models.IntegerField(null=True)
    tag_stats = JSONField(null=True)
    activity = JSONField(null=True)


class LadderStatistics(models.Model):
    ladder = models.OneToOneField(Ladder, on_delete=models.CASCADE, related_name='statistics')
    total_points = models.IntegerField(default=0)
    rank = models.IntegerField(null=True)


class BestSubmission(models.Model):
    profile = models.ForeignKey(UserProfile, related_name='best_submissions', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='best_submissions', on_delete=models.CASCADE)
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('profile', 'task'),)
