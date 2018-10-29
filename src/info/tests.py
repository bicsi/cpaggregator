from datetime import datetime

from django.test import TestCase

# Create your tests here.
from pytz import UTC

from data.models import User, UserHandle, Judge, Task, Submission
from info.models import TaskSheet


class TaskSheetTestCase(TestCase):
    today = datetime(2010, 1, 1, tzinfo=UTC)

    def setUp(self):
        # Create a task sheet.
        self.judge = Judge.objects.create(judge_id='ia')
        self.user = User.objects.create(username='user1')
        self.handle = UserHandle.objects.create(judge=self.judge, handle='ia_user', user=self.user)
        self.task = Task.objects.create(judge=self.judge, task_id='ia_task')
        self.sheet = TaskSheet.objects.create(slice_id='sheet')
        self.sheet.users.add(self.user)
        self.sheet.tasks.add(self.task)

    def test_best_submission_non_null(self):
        # Submission 1: score is None.
        Submission.objects.create(
            submission_id='1',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            verdict='WA')
        # Submission 2: score = 20.
        submission_bad_score = Submission.objects.create(
            submission_id='2',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            score=20,
            verdict='WA')
        self.assertCountEqual(self.sheet.get_best_submissions(),
                              [submission_bad_score])

    def test_best_submission_picks_ac(self):
        # Submission 1: verdict = WA.
        Submission.objects.create(
            submission_id='1',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            score=20,
            verdict='WA')
        # Submission 2: verdict = AC.
        submission_ok_score = Submission.objects.create(
            submission_id='2',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            verdict='AC')
        self.assertCountEqual(self.sheet.get_best_submissions(),
                              [submission_ok_score])

    def test_best_submission_picks_higher_score(self):
        # Submission 1: score = 20.
        Submission.objects.create(
            submission_id='1',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            score=20,
            verdict='WA')
        # Submission 2: score = 40.
        submission_better_score = Submission.objects.create(
            submission_id='2',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            score=50,
            verdict='WA')
        self.assertCountEqual(self.sheet.get_best_submissions(),
                              [submission_better_score])

