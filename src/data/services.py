import math
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from data.models import MethodTag, Task, Submission
from scraper.database import get_db
import scraper.services as scraper_services


def __update_task_info(db, task):
    print("Updating {}...".format(task))

    mongo_task_info = None
    for tries in range(3):
        mongo_task_info = db['tasks'].find_one({
            'judge_id': task.judge.judge_id,
            'task_id': task.task_id,
        })
        if mongo_task_info:
            break

        print(f'Task info for {task} not found in mongo.')
        print('Redirecting to scraper...')
        scraper_services.scrape_task_info(db, ":".join([task.judge.judge_id, task.task_id]))
        print('Retrying...')

    if not mongo_task_info:
        print(f'ERROR: Fetching task info for {task} failed!')
        return

    task.name = mongo_task_info['title']
    if 'time_limit' in mongo_task_info:
        task.time_limit_ms = mongo_task_info['time_limit']
    if 'memory_limit' in mongo_task_info:
        task.memory_limit_kb = mongo_task_info['memory_limit']

    for tag_id in mongo_task_info['tags']:
        try:
            tag = MethodTag.objects.get(tag_id=tag_id)
            task.tags.add(tag)
        except ObjectDoesNotExist:
            print('Skipped adding tag {}. Does not exist'.format(tag_id))

    task.save()


def __update_handle(db, handle):
    print(f"Updating {handle}...")

    mongo_handle_info = None
    for tries in range(3):
        mongo_handle_info = db['handles'].find_one({
            'judge_id': handle.judge.judge_id,
            'handle': handle.handle,
        })
        if mongo_handle_info:
            break

        print(f'Handle info for {handle} not found.')
        print('Redirecting to scraper...')
        scraper_services.scrape_handle_info(db, ":".join([handle.judge.judge_id, handle.handle]))

    if 'photo_url' in mongo_handle_info:
        handle.photo_url = mongo_handle_info['photo_url']
    else:
        handle.photo_url = None

    handle.save()


def __update_user(db, user):
    print(f"Updating {user.username}...")

    for user_handle in user.handles.all():
        judge = user_handle.judge
        # Get all submissions from mongodb.
        mongo_submissions = db['submissions'].find(dict(
            judge_id=judge.judge_id,
            author_id=user_handle.handle,
        ))
        # Migrate submission model to SQL model.
        for mongo_submission in mongo_submissions:
            try:
                task = Task.objects.get(
                    judge=judge,
                    task_id=mongo_submission['task_id'])
                update_dict = dict(
                    submitted_on=timezone.make_aware(mongo_submission['submitted_on']),
                    author=user_handle,
                    verdict=mongo_submission['verdict'],
                    language=mongo_submission.get('language'),
                    source_size=mongo_submission.get('source_size'),
                    score=mongo_submission.get('score'),
                    exec_time=mongo_submission.get('exec_time'),
                    memory_used=mongo_submission.get('memory_used'),
                )
                if update_dict['score'] and math.isnan(update_dict['score']):
                    update_dict['score'] = None

                # Filter values that are None.
                update_dict = dict(filter(lambda x: x[1] and x[1], update_dict.items()))

                _, created = Submission.objects.update_or_create(
                    submission_id=mongo_submission['submission_id'],
                    task=task, defaults=update_dict
                )

                if created:
                    print("Submission %s created." % mongo_submission['submission_id'])
            except ObjectDoesNotExist as e:
                pass
            except Exception as e:
                print('Submission %s failed. Error: %s' % (mongo_submission['submission_id'], e))


def update_tasks_info(tasks):
    db = get_db()
    for task in tasks:
        __update_task_info(db, task)


def update_handles(handles):
    db = get_db()
    for handle in handles:
        __update_handle(db, handle)


def update_users(users):
    db = get_db()
    for user in users:
        __update_user(db, user)