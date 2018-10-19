import datetime

from django.db import models
import data.models as data_models


class TaskSheet(models.Model):
    title = models.CharField(max_length=256, default="Results")
    slice_id = models.CharField(max_length=256, unique=True)
    created_at = models.DateTimeField(default=datetime.datetime.utcnow)
    users = models.ManyToManyField(data_models.User, blank=True)
    groups = models.ManyToManyField(data_models.UserGroup)
    tasks = models.ManyToManyField(data_models.Task)

    def get_all_users(self):
        result = list(self.users.all())
        for group in self.groups.all():
            result += list(group.members.all())
        return set(result)

    def get_all_submissions(self):
        return data_models.Submission.objects.filter(
            author__user__in=self.get_all_users(),
            task__in=self.tasks.all(),
        )

    def get_best_submissions(self):
        submissions = self.get_all_submissions() \
            .order_by('verdict', '-score', 'submitted_on')

        found = set()
        res = []
        for submission in submissions.all():
            key = (submission.task, submission.author)
            if key in found:
                continue
            found.add(key)
            res.append(submission)
        return sorted(res, key=lambda x: x.submitted_on)

    def __str__(self):
        return self.title


