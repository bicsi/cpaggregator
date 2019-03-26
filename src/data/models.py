from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.utils import timezone
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify

from . import managers

VERDICT_CHOICES = [
    ("AC", "Accepted"),
    ("CE", "Compile Error"),
    ("MLE", "Memory Limit Exceeded"),
    ("RE", "Runtime Error"),
    ("TLE", "Time Limit Exceeded"),
    ("WA", "Wrong Answer"),
]

VISIBILITY_CHOICES = [
    ("PUBLIC", "Public"),
    ("PRIVATE", "Private"),
]


class Judge(models.Model):
    judge_id = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=256)
    homepage = models.CharField(max_length=256)
    objects = managers.JudgeManager()

    def get_banner_url(self):
        return f'img/judge_logos/{self.judge_id}-big.png'

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

        handle_dict = {handle.judge.judge_id: handle for handle in self.handles.all()}
        judge_order = ['cf', 'ia', 'csa']
        for judge_id in judge_order:
            if judge_id in handle_dict and handle_dict[judge_id].photo_url:
                return handle_dict[judge_id].photo_url

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


class UserGroup(models.Model):
    group_id = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=256)
    members = models.ManyToManyField(UserProfile, related_name='assigned_groups')
    created_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(UserProfile, related_name='owned_groups', null=True, on_delete=models.SET_NULL)
    visibility = models.CharField(max_length=256, choices=VISIBILITY_CHOICES, default='PRIVATE')
    description = MarkdownxField(blank=True, null=True)

    # Model managers.
    objects = models.Manager()  # The default manager.
    public = managers.PublicGroupManager()

    @property
    def formatted_description(self):
        if not self.description:
            return ""
        return markdownify(self.description)

    @property
    def short_description(self):
        return self.description

    def is_owned_by(self, user):
        return user.is_superuser or user.profile == self.author

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
    modified_at = models.DateTimeField(auto_now=True)

    def name_or_id(self):
        if self.name:
            return self.name
        return self.task_id

    def get_url(self):
        if self.judge.judge_id == 'ojuz':
            return 'https://oj.uz/problem/view/%s' % self.task_id
        if self.judge.judge_id == 'csa':
            return 'https://csacademy.com/contest/archive/task/%s' % self.task_id
        if self.judge.judge_id == 'ia':
            return 'https://www.infoarena.ro/problema/%s' % self.task_id
        if self.judge.judge_id == 'cf':
            contest_id, task_letter = self.task_id.split('_')
            if int(contest_id) >= 100000:
                # Gym contest ids are always >= 100000
                return f'https://codeforces.com/gym/{contest_id}/problem/{task_letter.upper()}'
            return f'https://codeforces.com/contest/{contest_id}/problem/{task_letter.upper()}'
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
        if self.judge.judge_id == 'ojuz':
            return "https://oj.uz/profile/%s" % self.handle
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
    best = managers.BestSubmissionManager()
    best_recent = managers.BestRecentSubmissionManager()

    def get_url(self):
        if self.task.judge.judge_id == 'ojuz':
            return 'https://oj.uz/submission/%s' % self.submission_id
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
        unique_together = (('submission_id', 'author'),)
        ordering = ['-submitted_on']

    def __str__(self):
        return "%s's submission for %s [submitted on: %s, verdict: %s]" \
               % (self.author.user, self.task, self.submitted_on, self.verdict)
