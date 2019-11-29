from data.models import Submission, Task, UserHandle
from sklearn.preprocessing import LabelEncoder
from core.logging import log
import numpy as np
from scipy.optimize import minimize_scalar

from scraper import database


def make_dataset(augment_from_mongo):
    dataset = [(s.task.id, s.author.user.user.username)
               for s in Submission.objects.best().select_related(
                    'task', 'task__judge', 'author__user__user')]

    # Add mongodb submissions
    if augment_from_mongo:
        mongo_task_map = {":".join([t.judge.judge_id, t.task_id]): t
                          for t in Task.objects.select_related('judge').all()}
        mongo_author_map = {uh.handle: uh.user.user.username
                            for uh in UserHandle.objects.select_related("user__user").all()}

        log.info(f'Dataset size before augmentation: {len(dataset)}')
        for mongo_sub in database.find_submissions(database.get_db(), verdict='AC'):
            task = mongo_task_map.get(":".join([mongo_sub['judge_id'], mongo_sub['task_id']]))
            if task:
                username = mongo_author_map.get(mongo_sub['author_id'], mongo_sub['author_id'])
                dataset.append((task.id, username))
        dataset = set(dataset)
        log.info(f'Dataset size after augmentation: {len(dataset)}')

    tasks = [t for (t, _) in dataset]
    users = [u for (_, u) in dataset]
    return tasks, users


def compute_task_and_user_ratings(num_epochs=10, augment_from_mongo=True):
    tasks, users = make_dataset(augment_from_mongo)

    # Transform strs into ints.
    task_le = LabelEncoder().fit(tasks)
    user_le = LabelEncoder().fit(users)
    tasks = task_le.transform(tasks)
    users = user_le.transform(users)

    task_count = task_le.classes_.shape[0]
    user_count = user_le.classes_.shape[0]
    log.info(f'Tasks: {task_count} Users: {user_count}')

    task_users = [users[tasks == i] for i in range(task_count)]
    user_tasks = [tasks[users == i] for i in range(user_count)]

    def user_step(user_ratings, task_ratings, coef=1):
        new_user_ratings = user_ratings.copy()
        for user_i in range(user_count):
            tasks_solved = user_tasks[user_i]
            tasks_solved_ratings = task_ratings[tasks_solved]

            def neg_log_like(user_rating):
                user_rating = user_rating ** 2 + 1e-9
                log_like = np.log(user_rating) - tasks_solved_ratings / user_rating
                log_prior = -coef * user_rating
                return -(log_prior + np.sum(log_like))

            result = minimize_scalar(neg_log_like)
            if not result.success:
                log.warning('Minimization did not succeed.')
            new_user_ratings[user_i] = result.x
        return new_user_ratings

    def task_step(user_ratings, task_ratings, coef=3):
        new_task_ratings = task_ratings.copy()
        for task_i in range(task_count):
            users_solved = task_users[task_i]
            users_solved_ratings = user_ratings[users_solved]

            def neg_log_like(task_rating):
                task_rating = task_rating ** 2 + 1e-9
                log_like = -np.log(task_rating) - task_rating / users_solved_ratings
                log_prior = -coef / task_rating  # * 0.5 + np.log(2)
                return -(log_prior + np.sum(log_like))

            result = minimize_scalar(neg_log_like)
            if not result.success:
                log.warning('Minimization did not succeed.')
            new_task_ratings[task_i] = result.x
        return new_task_ratings

    task_ratings = np.ones((task_count,)) * 2
    user_ratings = np.ones((user_count,)) * 1
    for epoch in range(1, num_epochs + 1):
        log.info(f'Epoch {epoch}/{num_epochs}')
        user_ratings = user_step(user_ratings, task_ratings, coef=1)
        task_ratings = task_step(user_ratings, task_ratings, coef=4)

    task_ratings = {tn: tr for tn, tr in zip(task_le.classes_, task_ratings)}
    user_ratings = {un: ur for un, ur in zip(user_le.classes_, user_ratings)}

    return task_ratings, user_ratings
