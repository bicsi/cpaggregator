import json

from core.logging import log
from data.models import Submission, UserProfile, Task, Judge
from stats import utils
from .models import TaskStatistics, UserStatistics, BestSubmission

from celery import shared_task


def normalize_range(val, min=0, max=2e9, step=1):
    val = round(val) // step * step
    return min if val < min else (max if val > max else val)


@shared_task
def compute_task_statistics():
    """
    Computes a TaskStatistic object for each task,
    which it saves to the database
    """
    log.info('Computing task statistics...')

    BASE_SCORE = 100

    def get_multiplier(task):
        ac_count = None
        try:
            if task.statistics and task.statistics.users_solved_count:
                ac_count = task.statistics.users_solved_count
        except Task.statistics.RelatedObjectDoesNotExist:
            pass
        try:
            if task.judge_statistic and task.judge_statistic.accepted_submission_count:
                ac_count = task.judge_statistic.accepted_submission_count
        except Task.judge_statistic.RelatedObjectDoesNotExist:
            pass

        if ac_count is None:
            return 1.0
        return 1.0 / (ac_count + 10)

    for judge in Judge.objects.all():
        task_count = 0

        log.info(f"Computing task statistics for judge {judge}")
        for task in Task.objects.filter(judge=judge):
            users_solved_count = Submission.objects.best().filter(task=task, verdict='AC').count()
            users_tried_count = Submission.objects.best().filter(task=task).count()
            submission_count = Submission.objects.filter(task=task).count()
            favorited_count = task.favorite_users.count()

            TaskStatistics.objects.update_or_create(
                task=task, defaults=dict(
                    users_tried_count=users_tried_count,
                    users_solved_count=users_solved_count,
                    submission_count=submission_count,
                    favorited_count=favorited_count,
                ))
            task_count += 1

        if task_count == 0:
            continue

        mean_multiplier = 1.0 / task_count * sum([
            get_multiplier(task) for task in Task.objects.filter(judge=judge)
                .select_related('statistics', 'judge_statistic').all()])
        log.info(f'MEAN MULTIPLIER: {mean_multiplier}')

        for task in Task.objects.filter(judge=judge).select_related('statistics'):
            statistics = task.statistics
            statistics.difficulty_score = normalize_range(
                BASE_SCORE * get_multiplier(task) / mean_multiplier,
                min=5, max=2500, step=5)
            log.debug(f"{task}: {statistics.difficulty_score}")
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