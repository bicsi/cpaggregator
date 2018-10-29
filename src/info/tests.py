from datetime import datetime

from django.test import TestCase

# Create your tests here.
from data.models import User, UserHandle, Judge, Task, Submission
from info.models import TaskSheet


class TaskSheetTestCase(TestCase):
    def setUp(self):
        # Create necessary objects.
        self.judge = Judge.objects.create(judge_id='ia')
        self.user = User.objects.create(username='user1')
        self.handle = UserHandle.objects.create(judge=self.judge, handle='ia_user', user=self.user)
        self.task = Task.objects.create(judge=self.judge, task_id='ia_task')
        self.sheet = TaskSheet.objects.create(slice_id='sheet')
        self.sheet.users.add(self.user)
        self.sheet.tasks.add(self.task)
        self.today = datetime(2010, 1, 1)

        # Create submissions.
        self.submission_no_score = Submission(
            submission_id='1',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            verdict='WA')

        self.submission_bad_score = Submission(
            submission_id='2',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            score=20,
            verdict='WA')

        self.submission_ok_score = Submission(
            submission_id='3',
            submitted_on=self.today,
            task=self.task,
            author=self.handle,
            language='C++',
            source_size=1000,
            verdict='AC')

    def test_best_submission_non_null(self):
        self.submission_no_score.save()
        self.submission_bad_score.save()
        submissions = self.sheet.get_best_submissions()
        self.assertIn(self.submission_bad_score, submissions)
        self.assertNotIn(self.submission_no_score, submissions)

    def test_best_submission_picks_ac(self):
        self.submission_bad_score.save()
        self.submission_ok_score.save()
        submissions = self.sheet.get_best_submissions()
        self.assertIn(self.submission_ok_score, submissions)
        self.assertNotIn(self.submission_bad_score, submissions)

