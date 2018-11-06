from datetime import datetime

from django.test import TestCase

from pytz import UTC

from data.models import UserProfile, UserHandle, Judge, Task, Submission


class BestSubmissionManagerTestCase(TestCase):
    today = datetime(2010, 1, 1, tzinfo=UTC)

    def setUp(self):
        # Create an user and a task.
        self.judge = Judge.objects.create(judge_id='ia')
        self.user = UserProfile.objects.create(username='user1')
        self.handle = UserHandle.objects.create(judge=self.judge, handle='ia_user', user=self.user)
        self.task = Task.objects.create(judge=self.judge, task_id='ia_task')

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
        self.assertCountEqual(Submission.best.all(), [submission_bad_score])

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
        self.assertCountEqual(Submission.best.all(), [submission_ok_score])

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
        # Submission 2: score = 50.
        submission_better_score = Submission.objects.create(
            submission_id='2',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            score=50,
            verdict='WA')
        self.assertCountEqual(Submission.best.all(), [submission_better_score])
