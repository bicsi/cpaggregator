from data.models import Submission, UserProfile, Task
from .models import TaskStatistics, UserStatistics

from celery import shared_task


@shared_task
def compute_task_statistics():
    """
    Computes a TaskStatistic object for each task,
    which it saves to the database
    """
    for task in Task.objects.all():
        users_solved_count = Submission.best.filter(task=task, verdict='AC').count()
        users_tried_count = Submission.best.filter(task=task).count()
        submission_count = Submission.objects.filter(task=task).count()
        favorited_count = task.favorite_users.count()

        TaskStatistics.objects.update_or_create(task=task, defaults=dict(
            users_tried_count=users_tried_count,
            users_solved_count=users_solved_count,
            submission_count=submission_count,
            favorited_count=favorited_count,
        ))


@shared_task
def compute_user_statistics():
    """
    Computes UserStatistic objects,
    which it saves to the database
    """
    def make_user_stat(user):
        submissions = Submission.best.filter(author__in=user.handles.all())

        tasks_solved_count = submissions.filter(verdict='AC').count()
        tasks_tried_count = submissions.count()

        statistic, _ = UserStatistics.objects.update_or_create(
            user=user,
            defaults=dict(
                tasks_solved_count=tasks_solved_count,
                tasks_tried_count=tasks_tried_count,
            ))
        return statistic

    # Make statistics.
    user_statistics = [make_user_stat(user) for user in UserProfile.objects.all()]

    # Compute ranks.
    old_best = -1
    current_rank = 1
    next_rank = 1
    for statistic in sorted(user_statistics, key=lambda stat: stat.tasks_solved_count, reverse=True):
        if statistic.tasks_solved_count < old_best:
            current_rank = next_rank
        old_best = statistic.tasks_solved_count
        statistic.rank = current_rank
        next_rank += 1

    # Save.
    for statistic in user_statistics:
        statistic.save(force_update=True)