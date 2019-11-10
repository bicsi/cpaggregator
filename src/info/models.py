from django.db import models
from django.utils import timezone
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify

from data.models import UserGroup, Submission, Task, UserProfile
from . import managers


class TaskSheet(models.Model):
    title = models.CharField(max_length=256, default="Results")
    sheet_id = models.CharField(max_length=256, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    description = MarkdownxField(blank=True, null=True)
    tasks = models.ManyToManyField(Task, through='TaskSheetTask')
    is_public = models.BooleanField(default=False)
    author = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.CASCADE)

    @property
    def formatted_description(self):
        return markdownify(self.description)

    def is_owned_by(self, user):
        if user.is_superuser:
            return True
        if user.profile == self.author:
            return True
        if self.assignment and self.assignment.group.is_owned_by(user):
            return True
        return False

    def __str__(self):
        return self.title


class TaskSheetTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    sheet = models.ForeignKey(TaskSheet, on_delete=models.CASCADE)
    ordering_id = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.sheet} -> {self.task.judge.judge_id}:{self.task.task_id}'

    class Meta:
        db_table = 'info_tasksheet_x_task'
        unique_together = (('task', 'sheet'),)
        ordering = ['ordering_id']


class Assignment(models.Model):
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    sheet = models.OneToOneField(TaskSheet, on_delete=models.CASCADE)
    assigned_on = models.DateTimeField()
    end_on = models.DateTimeField(blank=True, null=True)
    ordering_id = models.PositiveIntegerField(blank=True, null=True)
    use_best_recent = models.BooleanField(default=False)
    hide_submissions_before_assigned = models.BooleanField(default=False)

    # Managers.
    objects = managers.AssignmentQuerySet.as_manager()

    def get_all_users(self):
        return self.group.members.all()

    def _submissions(self):
        submissions = Submission.objects.filter(
            author__user__in=self.get_all_users(),
            task__in=self.sheet.tasks.all())
        if self.hide_submissions_before_assigned:
            submissions = submissions.filter(submitted_on__gt=self.assigned_on)
        if self.end_on:
            submissions = submissions.filter(submitted_on__lt=self.end_on)
        return submissions

    def get_all_submissions(self):
        return self._submissions().order_by('submitted_on')

    def get_best_submissions(self):
        return self._submissions().best(use_recent=self.use_best_recent).order_by('submitted_on')

    def get_all_judges(self):
        return {task.judge for task in self.sheet.tasks.all()}

    def is_future(self):
        return self.assigned_on > timezone.now()

    def __str__(self):
        return '{} assigned to {}'.format(self.sheet, self.group)

    class Meta:
        unique_together = (('group', 'sheet'),)
        ordering = ('ordering_id', '-assigned_on')


class FavoriteTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='favorite_users')
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='favorite_tasks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('task', 'profile'),)


class CustomTaskTag(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='custom_tags')
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='custom_tags')
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=32)

    class Meta:
        unique_together = (('task', 'profile', 'name'),)

    def __str__(self):
        return f"#{self.name} for {self.task} from {self.profile}"


