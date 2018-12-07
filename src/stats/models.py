from django.db import models

from data.models import Task


class TaskStatistics(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='statistics')
    users_tried_count = models.IntegerField()
    users_solved_count = models.IntegerField()
    submission_count = models.IntegerField()

    @property
    def mean_submission_count(self):
        return self.submission_count / self.users_tried_count

    @property
    def acceptance_rate(self):
        return self.users_solved_count / self.users_tried_count

