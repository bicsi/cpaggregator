from data.models import Submission
from .models import TaskStatistics


def compute_task_statistics(task):
    """
    Computes a TaskStatistic object for a given task,
    which it saves to the database
    :param task: the task for which to compute the statistics
    """
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