import json
from types import SimpleNamespace
from typing import NamedTuple, List

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

    class TaskData(SimpleNamespace):
        users_solved: List[UserProfile]
        difficulty: float

    # Build task data.
    task_data = {}
    for submission in Submission.objects.best().accepted().select_related('author').all():
        task = task_data.get(submission.task, TaskData(
            users_solved=[],
            difficulty=10.
        ))
        task.users_solved.append(submission.author.user)
        task_data[submission.task] = task

    users_rating = {}
    for user in UserProfile.objects.all():
        users_rating[user] = 1.0

    for iteration in range(10):
        for user in users_rating:
            users_rating[user] = 0.
        for task in task_data.values():
            for user in task.users_solved:
                users_rating[user] += task.difficulty

        sum_difficulty = 0.
        for task in task_data.values():
            ratings = sorted([users_rating[user] for user in task.users_solved])
            clipped = ratings[len(ratings) // 10:len(ratings) // 4 + 1]
            task.difficulty = 50.0 / len(ratings) + sum(clipped) / len(clipped)
            sum_difficulty += task.difficulty

        norm_factor = sum_difficulty / len(task_data)
        for task in task_data.values():
            task.difficulty = task.difficulty / norm_factor

    max_difficulty = max([task.difficulty for task in task_data.values()])

    for statistics in TaskStatistics.objects.all():
        difficulty = max_difficulty
        if statistics.task in task_data:
            difficulty = task_data[statistics.task].difficulty
        difficulty_score = min(2500, max(5, 5 * round(BASE_SCORE * difficulty / 5)))
        print(f'Task: {statistics.task} score: {difficulty_score}')
        statistics.difficulty_score = difficulty_score
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
