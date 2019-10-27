import json

from data.models import Submission, UserProfile, Task
from stats import utils
from .models import TaskStatistics, UserStatistics, BestSubmission

from celery import shared_task


@shared_task
def compute_task_statistics():
    """
    Computes a TaskStatistic object for each task,
    which it saves to the database
    """

    BASE_SCORE = 100
    judge_to_total_solved = {}
    judge_to_task_count = {}

    for task in Task.objects.all():
        users_solved_count = Submission.objects.best().filter(task=task, verdict='AC').count()
        users_tried_count = Submission.objects.best().filter(task=task).count()
        submission_count = Submission.objects.filter(task=task).count()
        favorited_count = task.favorite_users.count()

        judge = task.judge
        judge_to_total_solved[judge] = judge_to_total_solved.get(judge, 0) + 1.0 / (users_solved_count + 10.0)
        judge_to_task_count[judge] = judge_to_task_count.get(judge, 0) + 1

        TaskStatistics.objects.update_or_create(task=task, defaults=dict(
            users_tried_count=users_tried_count,
            users_solved_count=users_solved_count,
            submission_count=submission_count,
            favorited_count=favorited_count
        ))

    for task in Task.objects.all():
        if judge_to_task_count[task.judge] == 0:
            continue

        statistics = task.statistics
        users_solved_count = statistics.users_solved_count
        mean_users_solved_count = judge_to_total_solved[task.judge] / judge_to_task_count[task.judge]
        multiplier = 1.0 / (users_solved_count + 10.0) / mean_users_solved_count
        statistics.difficulty_score = min(2500, 5 * max(1, round(BASE_SCORE * multiplier / 5)))

        statistics.save()


@shared_task
def compute_best_submissions():
    print('[TASK] Computing best submissions...')
    for submission in Submission.objects.best().all():
        BestSubmission.objects.update_or_create(
            task=submission.task,
            profile=submission.author.user,
            defaults={'submission': submission})


@shared_task
def compute_user_statistics():
    """
    Computes UserStatistic objects,
    which it saves to the database
    """
    def make_user_stat(user):
        submissions = Submission.objects.best().filter(author__in=user.handles.all())

        tasks_solved_count = submissions.filter(verdict='AC').count()
        tasks_tried_count = submissions.count()
        activity_dict = utils.build_activity_dict(user)
        tag_stats_dict = utils.build_tag_stats_dict(user)

        total_points = 0
        for submission in submissions.filter(verdict='AC').all():
            total_points += submission.task.statistics.difficulty_score

        statistic, _ = UserStatistics.objects.update_or_create(
            user=user,
            defaults=dict(
                tasks_solved_count=tasks_solved_count,
                tasks_tried_count=tasks_tried_count,
                total_points=total_points,
                activity=json.dumps(activity_dict),
                tag_stats=json.dumps(tag_stats_dict),
            ))
        return statistic

    # Make statistics.
    user_statistics = [make_user_stat(user) for user in UserProfile.objects.all()]

    # Compute ranks.
    old_best = -1
    current_rank = 1
    next_rank = 1
    for statistic in sorted(user_statistics, key=lambda stat: stat.total_points, reverse=True):
        if statistic.total_points < old_best:
            current_rank = next_rank
        old_best = statistic.total_points
        statistic.rank = current_rank
        next_rank += 1

    # Save.
    for statistic in user_statistics:
        statistic.save(force_update=True)