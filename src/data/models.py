from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string

from data.managers import BestSubmissionManager, JudgeManager

VERDICT_CHOICES = [
    ("AC", "Accepted"),
    ("CE", "Compile Error"),
    ("MLE", "Memory Limit Exceeded"),
    ("RE", "Runtime Error"),
    ("TLE", "Time Limit Exceeded"),
    ("WA", "Wrong Answer"),
]


class Judge(models.Model):
    judge_id = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=256)
    homepage = models.CharField(max_length=256)
    objects = JudgeManager()

    def get_logo_url(self):
        return f'img/judge_logos/{self.judge_id}.svg'

    def __str__(self):
        return self.name


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>.
    return 'user_{0}/{1}'.format(instance.user.username, filename)


class UserProfile(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='profile')
    first_name = models.CharField(max_length=256, null=True, blank=True)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(upload_to=user_directory_path, blank=True)

    @property
    def username(self):
        if self.user:
            return self.user.username
        return str(self.id)

    def avatar_url_or_default(self):
        if self.avatar:
            return self.avatar.url

        for handle in self.handles.all():
            if handle.photo_url:
                return handle.photo_url

        return static("img/user-avatar.svg")

    def get_display_name(self):
        if self.first_name and self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        return self.username

    def get_solved_tasks(self):
        tasks = []
        for handle in self.handles.all():
            for submission in handle.submission_set.all():
                if submission.verdict == 'AC':
                    tasks.append(submission.task)
        return set(tasks)

    def get_submitted_tasks(self):
        tasks = []
        for handle in self.handles.all():
            for submission in handle.submission_set.all():
                tasks.append(submission.task)
        return set(tasks)

    def get_unsolved_tasks(self):
        return self.get_submitted_tasks() - self.get_solved_tasks()

    def __str__(self):
        return self.get_display_name()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            first_name=instance.first_name,
            last_name=instance.last_name)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile') and instance.profile is not None:
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance, username=instance.username)


class UserGroup(models.Model):
    group_id = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=256)
    members = models.ManyToManyField(UserProfile, related_name='assigned_groups')
    created_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(UserProfile, related_name='groups_owned', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class MethodTag(models.Model):
    tag_id = models.CharField(max_length=256, unique=True)
    tag_name = models.CharField(max_length=256)

    def __str__(self):
        return self.tag_name


class Task(models.Model):
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=256)
    name = models.CharField(null=True, blank=True, max_length=256)
    time_limit_ms = models.IntegerField(null=True, blank=True)
    memory_limit_kb = models.IntegerField(null=True, blank=True)
    tags = models.ManyToManyField(MethodTag, blank=True)

    def name_or_id(self):
        if self.name:
            return self.name
        return self.task_id

    def get_url(self):
        if self.judge.judge_id == 'csa':
            return 'https://csacademy.com/contest/archive/task/%s' % self.task_id
        if self.judge.judge_id == 'ia':
            return 'https://www.infoarena.ro/problema/%s' % self.task_id
        if self.judge.judge_id == 'cf':
            contest_id, task_letter = self.task_id.split('_')
            return 'https://codeforces.com/contest/%s/problem/%s' % (contest_id, task_letter)
        return None

    class Meta:
        unique_together = (('judge', 'task_id'),)

    def __str__(self):
        return "{}:{}".format(self.judge.judge_id, self.task_id)


class UserHandle(models.Model):
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    handle = models.CharField(max_length=256)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='handles')
    photo_url = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        unique_together = (('judge', 'handle'),)

    def get_url(self):
        if self.judge.judge_id == 'csa':
            if self.handle.startswith('_uid_'):
                return "https://csacademy.com/userid/%s" % self.handle[5:]
            return "https://csacademy.com/user/%s" % self.handle
        if self.judge.judge_id == 'ia':
            return "https://www.infoarena.ro/utilizator/%s" % self.handle
        if self.judge.judge_id == 'cf':
            return "https://codeforces.com/profile/%s" % self.handle

    def __str__(self):
        return "%s:%s" % (self.judge.judge_id, self.handle)


class Submission(models.Model):
    submission_id = models.CharField(max_length=256)
    submitted_on = models.DateTimeField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    author = models.ForeignKey(UserHandle, on_delete=models.CASCADE)
    language = models.CharField(max_length=256)
    source_size = models.IntegerField(null=True, blank=True)
    verdict = models.CharField(max_length=256, choices=VERDICT_CHOICES)
    score = models.IntegerField(null=True, blank=True)
    exec_time = models.IntegerField(null=True, blank=True)
    memory_used = models.IntegerField(null=True, blank=True)

    # Managers.
    objects = models.Manager()  # The default manager.
    best = BestSubmissionManager()

    def get_url(self):
        if self.task.judge.judge_id == 'csa':
            return 'https://csacademy.com/submission/%s' % self.submission_id
        if self.task.judge.judge_id == 'ia':
            return 'https://www.infoarena.ro/job_detail/%s' % self.submission_id
        if self.task.judge.judge_id == 'cf':
            contest_id, _ = self.task.task_id.split('_')
            return 'https://codeforces.com/contest/%s/submission/%s' % (contest_id, self.submission_id)

        print("Bad", self.submission_id)
        return None

    class Meta:
        unique_together = (('task', 'submission_id'),)
        ordering = ['-submitted_on']

    def __str__(self):
        return "%s's submission for %s [submitted on: %s, verdict: %s]" \
               % (self.author.user, self.task, self.submitted_on, self.verdict)
