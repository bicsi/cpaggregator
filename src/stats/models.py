from django.db import models
import math
from data.models import Task


class TaskStatistics(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='statistics')
    users_tried_count = models.IntegerField(default=0)
    users_solved_count = models.IntegerField(default=0)
    submission_count = models.IntegerField(default=0)
    favorited_count = models.IntegerField(default=0)

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

