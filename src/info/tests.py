from datetime import datetime, timedelta

from django.test import TestCase

from pytz import UTC

from data.models import UserProfile, UserHandle, Judge, Task, Submission
from info.models import TaskSheet


class BestSubmissionManagerTestCase(TestCase):
    today = datetime(2010, 1, 1, tzinfo=UTC)

    def setUp(self):
        # Create some users and a task.
        self.judge = Judge.objects.create(judge_id='ia')
        self.user1 = UserProfile.objects.create(username='user1')
        self.user2 = UserProfile.objects.create(username='user2')
        self.handle1 = UserHandle.objects.create(judge=self.judge, handle='ia_user1', user=self.user1)
        self.handle2 = UserHandle.objects.create(judge=self.judge, handle='ia_user2', user=self.user2)
        self.task = Task.objects.create(judge=self.judge, task_id='ia_task')
        # Create a task sheet.
        self.sheet = TaskSheet.objects.create(sheet_id='sheet')
        self.sheet.users.add(self.user1)
        self.sheet.users.add(self.user2)
        self.sheet.tasks.add(self.task)

    def test_submission_sanity(self):
        # Submission 1: score is None.
        user1_no_score = Submission.objects.create(
            submission_id='1',
            submitted_on=self.today,
            task=self.task,
            author=self.handle1,
            language='C++',
            source_size=1000,
            verdict='WA')
        # Submission 2: score = 20.
        user1_bad_score = Submission.objects.create(
            submission_id='2',
            submitted_on=self.today,
            task=self.task,
            author=self.handle1,
            language='C++',
            source_size=1000,
            score=20,
            verdict='WA')
        # Submission 3: score is None.
        user2_no_score = Submission.objects.create(
            submission_id='3',
            submitted_on=self.today,
            task=self.task,
            author=self.handle2,
            language='C++',
            source_size=1000,
            verdict='WA')

        self.assertCountEqual(list(self.sheet.get_best_submissions().all()),
                              [user1_bad_score, user2_no_score])
        self.assertCountEqual(list(self.sheet.get_all_submissions().all()),
                              [user1_bad_score, user1_no_score, user2_no_score])

    def test_submission_order_by_date(self):
        # Submission 1: 10 minutes ago.
        submission_late = Submission.objects.create(
            submission_id='1',
            submitted_on=self.today - timedelta(minutes=10),
            task=self.task,
            author=self.handle1,
            language='C++',
            source_size=1000,
            score=20,
            verdict='WA')
        # Submission 2: 20 minutes ago.
        submission_early = Submission.objects.create(
            submission_id='2',
            submitted_on=self.today - timedelta(minutes=20),
            task=self.task,
            author=self.handle2,
            language='C++',
            source_size=1000,
            verdict='AC')

        self.assertListEqual(list(self.sheet.get_best_submissions().all()),
                             [submission_early, submission_late])
        self.assertListEqual(list(self.sheet.get_all_submissions().all()),
                             [submission_early, submission_late])
