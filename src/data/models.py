
from django.db import models
from django.utils import timezone

JUDGE_CHOICES = [
    ("ac", "AtCoder"),
    ("ia", "Infoarena"),
    ("poj", "POJ"),
    ("cf", "Codeforces"),
]

VERDICT_CHOICES = [
    ("AC", "Accepted"),
    ("CE", "Compile Error"),
    ("MLE", "Memory Limit Exceeded"),
    ("RE", "Runtime Error"),
    ("TLE", "Time Limit Exceeded"),
    ("WA", "Wrong Answer"),
]


class Judge(models.Model):
    judge_id = models.CharField(max_length=256, choices=JUDGE_CHOICES, unique=True)
    name = models.CharField(max_length=256)
    homepage = models.CharField(max_length=256)

    def get_logo_url(self):
        return 'img/judge_logos/%s.png' % self.judge_id

    def __str__(self):
        return self.name


class User(models.Model):
    username = models.CharField(max_length=256, unique=True)
    first_name = models.CharField(max_length=256, null=True)
    last_name = models.CharField(max_length=256, null=True)
    created_at = models.DateTimeField(default=timezone.now)

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
    group_id = models.CharField(max_length=256)
    name = models.CharField(max_length=256, unique=True)
    members = models.ManyToManyField(User)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Task(models.Model):
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=256)
    name = models.CharField(null=True, max_length=256)

    def get_url(self):
        if self.judge.judge_id == 'csa':
            return 'https://csacademy.com/contest/archive/task/%s' % self.task_id
        if self.judge.judge_id == 'ia':
            return 'https://www.infoarena.ro/problema/%s' % self.task_id
        return None

    class Meta:
        unique_together = (('judge', 'task_id'),)

    def __str__(self):
        return "%s:%s" % (self.judge.judge_id, self.task_id)


class UserHandle(models.Model):
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    handle = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='handles')

    class Meta:
        unique_together = (('judge', 'handle'),)

    def __str__(self):
        return "%s:%s" % (self.judge.judge_id, self.handle)


class Submission(models.Model):
    submission_id = models.CharField(max_length=256)
    submitted_on = models.DateTimeField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    author = models.ForeignKey(UserHandle, on_delete=models.CASCADE)
    language = models.CharField(max_length=256)
    source_size = models.IntegerField(null=True)
    verdict = models.CharField(max_length=256, choices=VERDICT_CHOICES)
    score = models.IntegerField(null=True)
    exec_time = models.IntegerField(null=True)
    memory_used = models.IntegerField(null=True)

    def get_url(self):
        if self.task.judge.judge_id == 'csa':
            return 'https://csacademy.com/submission/%s' % self.submission_id
        if self.task.judge.judge_id == 'ia':
            return 'https://www.infoarena.ro/job_detail/%s' % self.submission_id
        print("Bad", self.submission_id)
        return None

    class Meta:
        unique_together = (('task', 'submission_id'),)
        ordering = ['-submitted_on']

    def __str__(self):
        return "%s's submission for %s [submitted on: %s, verdict: %s]" \
               % (self.author.user, self.task, self.submitted_on, self.verdict)
