from datetime import datetime, timedelta

from django.test import TestCase

from pytz import UTC

from cpaggregator import settings
from data.models import UserProfile, UserHandle, Judge, Task, Submission, UserGroup
from info.models import TaskSheet, Assignment, TaskSheetTask

from model_mommy import mommy


class AssignmentTestCase(TestCase):
    now = datetime(2010, 1, 1, tzinfo=UTC)
    settings.USE_CELERY = False

    def setUp(self):
        # Create some users and a task.
        judge = mommy.make(Judge, judge_id='ia')
        self.handles = [mommy.make(UserHandle, judge=judge) for _ in range(2)]
        self.task = mommy.make(Task, judge=judge, task_id='task')

        # Create an assignment.
        self.assignment = mommy.make(Assignment)
        for handle in self.handles:
            self.assignment.group.members.add(handle.user)
        mommy.make(TaskSheetTask, task=self.task, sheet=self.assignment.sheet)

    def test_sanity(self):
        submissions = [mommy.make(Submission, task=self.task, author=handle)
                       for handle in self.handles]
        self.assertCountEqual(list(self.assignment.get_all_submissions()), submissions)
        self.assertCountEqual(list(self.assignment.get_best_submissions()), submissions)

    def test_best_submissions(self):
        # Submission 1: score is None.
        user0_no_score = mommy.make(
            Submission, task=self.task,
            author=self.handles[0], verdict='WA')

        # Submission 2: score = 20.
        user0_bad_score = mommy.make(
            Submission, task=self.task,
            author=self.handles[0], score=20, verdict='WA')

        # Submission 3: score is None.
        user1_no_score = mommy.make(
            Submission, task=self.task,
            author=self.handles[1], verdict='WA')

        self.assertCountEqual(list(self.assignment.get_best_submissions().all()),
                              [user0_bad_score, user1_no_score])
        self.assertCountEqual(list(self.assignment.get_all_submissions().all()),
                              [user0_bad_score, user0_no_score, user1_no_score])

    def test_best_recent_submissions(self):
        # Submission 1: 2 minutes ago
        early_submission = mommy.make(
            Submission, task=self.task,
            submitted_on=self.now - timedelta(minutes=2),
            author=self.handles[0], verdict='AC')

        # Submission 2: 1 minute ago
        late_submission = mommy.make(
            Submission, task=self.task,
            submitted_on=self.now - timedelta(minutes=1),
            author=self.handles[0], verdict='AC')

        self.assertCountEqual(list(self.assignment.get_best_submissions().all()),
                              [early_submission])
        self.assignment.use_best_recent = True
        self.assignment.save()
        self.assertCountEqual(list(self.assignment.get_best_submissions().all()),
                              [late_submission])

    def test_submissions_are_ordered_by_date(self):
        # Submission 1: 10 minutes ago.
        submission_late = mommy.make(
            Submission, task=self.task,
            submitted_on=self.now - timedelta(minutes=10),
            author=self.handles[0], score=20, verdict='WA')

        # Submission 2: 20 minutes ago.
        submission_early = mommy.make(
            Submission, task=self.task,
            submitted_on=self.now - timedelta(minutes=20),
            author=self.handles[1], verdict='AC')

        self.assertListEqual(list(self.assignment.get_best_submissions().all()),
                             [submission_early, submission_late])
        self.assertListEqual(list(self.assignment.get_all_submissions().all()),
                             [submission_early, submission_late])

    def test_submissions_after_deadline_not_counted(self):
        self.assignment.assigned_on = self.now - timedelta(days=3)
        self.assignment.end_on = self.now - timedelta(days=1)
        self.assignment.save()

        # Submission 1: before deadline.
        submission_before = mommy.make(
            Submission, task=self.task,
            author=self.handles[0],
            submitted_on=self.now - timedelta(days=2),
            score=20, verdict='WA')

        # Submission 2: after deadline
        mommy.make(
            Submission, task=self.task,
            author=self.handles[0],
            submitted_on=self.now - timedelta(hours=23),
            score=100, verdict='AC')

        # Submission 3: after deadline
        mommy.make(
            Submission, task=self.task,
            author=self.handles[1],
            submitted_on=self.now - timedelta(hours=22))

        self.assertCountEqual(list(self.assignment.get_best_submissions().all()), [submission_before])
        self.assertCountEqual(list(self.assignment.get_all_submissions().all()), [submission_before])

    def test_submissions_before_assigned_not_counted(self):
        self.assignment.assigned_on = self.now - timedelta(days=3)
        self.assignment.hide_submissions_before_assigned = True
        self.assignment.save()

        # Submission 1: before start.
        mommy.make(
            Submission, task=self.task,
            author=self.handles[0],
            submitted_on=self.now - timedelta(days=4),
            score=20, verdict='WA')

        # Submission 2: after start
        submission_after = mommy.make(
            Submission, task=self.task,
            author=self.handles[0],
            submitted_on=self.now - timedelta(days=2),
            score=100, verdict='AC')

        # Submission 3: after start
        mommy.make(
            Submission, task=self.task,
            author=self.handles[1],
            submitted_on=self.now - timedelta(days=4))

        self.assertCountEqual(list(self.assignment.get_best_submissions().all()), [submission_after])
        self.assertCountEqual(list(self.assignment.get_all_submissions().all()), [submission_after])
