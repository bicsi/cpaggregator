import re

from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.utils import timezone
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from django.contrib.postgres.fields import JSONField

from core import urlresolvers
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


class UserProfileManager(models.Manager):
    def get_queryset(self):
        return super(UserProfileManager, self).get_queryset().prefetch_related('user')


class UserProfile(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='profile')
    first_name = models.CharField(max_length=256, null=True, blank=True)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to=user_directory_path, blank=True)

    objects = UserProfileManager()

    @property
    def username(self):
        if self.user:
            return self.user.username
        return str(self.id)

    def avatar_url_or_default(self):
        if self.avatar:
            return self.avatar.url

        handle_dict = {handle.judge.judge_id: handle
                       for handle in self.handles.select_related('judge').all()}
        judge_order = ['cf', 'ia', 'csa']
        for judge_id in judge_order:
            if judge_id in handle_dict and handle_dict[judge_id].photo_url:
                return handle_dict[judge_id].photo_url

        return static("img/user-avatar.svg")

    def get_display_name(self):
        if self.first_name and self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        return self.username

    def __str__(self):
        return self.get_display_name()


class UserGroup(models.Model):
    group_id = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=256)
    members = models.ManyToManyField(UserProfile, related_name='assigned_groups', through='GroupMember')
    created_at = models.DateTimeField(auto_now_add=True)
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
        if user.is_superuser:
            return True
        if user.profile == self.author:
            return True
        if GroupMember.objects.filter(profile=user.profile, group=self, role='owner').exists():
            return True

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=64,
                            choices=[('member', 'member'), ('owner', 'owner')],
                            default='member')

    def __str__(self):
        return f'{self.profile} is {self.role} in {self.group}'

    class Meta:
        unique_together = (('profile', 'group'),)


class MethodTag(models.Model):
    tag_id = models.CharField(max_length=256, unique=True)
    tag_name = models.CharField(max_length=256)

    def __str__(self):
        return self.tag_name


class TaskSource(models.Model):
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    source_id = models.SlugField(max_length=256)
    name = models.CharField(max_length=1024)
    public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.judge.judge_id}] {self.name}"

    class Meta:
        unique_together = (('judge', 'source_id'),)


class TaskManager(models.Manager):
    def get_queryset(self):
        return super(TaskManager, self).get_queryset().select_related('judge')

    def filter_path(self, path):
        judge_id, task_id = path.split('/', 1)
        return self.get_queryset().filter(judge__judge_id=judge_id, task_id=task_id)


class Task(models.Model):
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=256)
    name = models.CharField(null=True, blank=True, max_length=256)
    tags = models.ManyToManyField(MethodTag, blank=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.ForeignKey(TaskSource, blank=True, null=True, on_delete=models.SET_NULL)

    objects = TaskManager()

    def name_or_id(self):
        if self.name:
            return self.name
        return self.task_id

    def get_url(self):
        return urlresolvers.get_task_url(
            self.judge.judge_id, self.task_id)

    def get_path(self):
        return f"{self.judge.judge_id}/{self.task_id}"

    class Meta:
        unique_together = (('judge', 'task_id'),)

    def __str__(self):
        return f"{self.judge.judge_id}/{self.task_id} <{self.name or 'UNKNOWN TITLE'}>"


class TaskStatement(models.Model):
    task = models.OneToOneField(Task, related_name='statement', on_delete=models.CASCADE)
    text = models.TextField()
    examples = JSONField(null=True, blank=True)
    input_file = models.CharField(max_length=256, null=True, blank=True)
    output_file = models.CharField(max_length=256, null=True, blank=True)
    memory_limit_kb = models.IntegerField(null=True, blank=True)
    time_limit_ms = models.IntegerField(null=True, blank=True)
    modified_by_user = models.BooleanField(default=False)

    @property
    def formatted(self):
        ret = markdownify(self.text)
        ret = re.sub(r"<code>\$([^<>]*)\$<\/code>", r'\\(\g<1>\\)', ret)
        ret = f"<div class=\"markdown\">{ret}</div>"
        return ret

    def __str__(self):
        return f"Task statement for {self.task}"


class JudgeTaskStatistic(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='judge_statistic')
    first_submitted_on = models.DateTimeField(null=True, blank=True)
    total_submission_count = models.IntegerField(null=True, blank=True)
    accepted_submission_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Judge statistic for {self.task}"


class UserHandle(models.Model):
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    handle = models.CharField(max_length=256)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='handles')
    photo_url = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        unique_together = (('judge', 'handle'),)

    def get_url(self):
        return urlresolvers.get_handle_url(
            self.judge.judge_id, self.handle)

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

    objects = managers.SubmissionQuerySet().as_manager()

    def get_url(self):
        return urlresolvers.get_submission_url(
            self.task.judge.judge_id, self.task.task_id, self.submission_id)

    def is_ac(self):
        return self.verdict == 'AC'

    class Meta:
        unique_together = (('submission_id', 'author'),)
        ordering = ['-submitted_on']

    def __str__(self):
        return "%s's submission for %s [submitted on: %s, verdict: %s]" \
               % (self.author.user, self.task, self.submitted_on, self.verdict)
