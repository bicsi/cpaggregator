import json

from django.core.exceptions import ObjectDoesNotExist

from core.logging import log
from data.models import Submission, UserProfile, Task, Judge
from ladders.models import Ladder, LadderTask
from stats import utils, multipliers
from .models import TaskStatistics, UserStatistics, BestSubmission, LadderStatistics

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

    task_ratings, user_ratings = multipliers.compute_task_and_user_ratings(
        augment_from_mongo=False)
    default_multiplier = max(task_ratings.values())

    def get_multiplier(task):
        return task_ratings.get(task.id, default_multiplier)

    task_count = 0
    for task in Task.objects.all():
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
        return

    mean_multiplier = sum([
        get_multiplier(task) for task in Task.objects.all()])
    mean_multiplier /= task_count

    log.info(f'MEAN MULTIPLIER: {mean_multiplier}')

    scores = {task: normalize_range(BASE_SCORE * get_multiplier(task) / mean_multiplier,
                                    min=5, max=1000, step=5)
              for task in Task.objects.all()}
    log.info(scores)

    for task in Task.objects.select_related('statistics'):
        statistics = task.statistics
        statistics.difficulty_score = scores[task]
        statistics.save()


def compute_ranks(elems, key, reverse=False):
    elems = list(elems)
    old_best = None
    current_rank = 1
    next_rank = 1
    ranks = [None] * len(elems)
    for idx in sorted(range(len(elems)), key=lambda x: key(elems[x]), reverse=reverse):
        elem_key = key(elems[idx])
        if old_best is None or elem_key != old_best:
            current_rank = next_rank
        old_best = elem_key
        ranks[idx] = current_rank
        next_rank += 1
    return ranks


@shared_task
def compute_ladder_statistics():
    log.info('Computing ladder statistics...')

    scores = {}
    for task in (LadderTask.objects
            .filter(status=LadderTask.Status.COMPLETED)
            .select_related('task', 'task__statistics', 'ladder')):
        ladder = task.ladder
        score = scores.get(ladder, 0)
        try:
            score += task.task.statistics.difficulty_score
        except ObjectDoesNotExist:
            pass
        scores[ladder] = score

    stats = []
    for ladder in Ladder.objects.all():
        stat, _ = LadderStatistics.objects.update_or_create(
            ladder=ladder,
            defaults=dict(
                total_points=scores.get(ladder, 0)
            ))
        stats.append(stat)

    ranks = compute_ranks(stats, key=lambda x: x.total_points, reverse=True)
    for stat, rank in zip(stats, ranks):
        stat.rank = rank

    for stat in stats:
        stat.save(force_update=True)


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
            try:
                total_points += submission.task.statistics.difficulty_score
            except ObjectDoesNotExist:
                pass

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
    ranks = compute_ranks(user_statistics, key=lambda stat: stat.total_points, reverse=True)
    # Save.
    for stat, rank in zip(user_statistics, ranks):
        stat.rank = rank

    for stat in user_statistics:
        stat.save(force_update=True)

