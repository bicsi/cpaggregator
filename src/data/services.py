import math
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.text import slugify

from data.models import MethodTag, Task, Submission, UserProfile, UserHandle, TaskSource
from scraper.database import get_db
import scraper.services as scraper_services

from celery import shared_task


def __update_task_info(db, task):
    print("Updating {}...".format(task))

    mongo_task_info = None
    for tries in range(3):
        mongo_task_info = db['tasks'].find_one({
            'judge_id': task.judge.judge_id.lower(),
            'task_id': task.task_id.lower(),
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

    for tag_id in mongo_task_info.get('tags', []):
        try:
            tag = MethodTag.objects.get(tag_id=tag_id)
            task.tags.add(tag)
        except ObjectDoesNotExist:
            print('Skipped adding tag {}. Does not exist'.format(tag_id))

    if 'source' in mongo_task_info:
        source_id, _ = slugify(mongo_task_info['source'])
        source = TaskSource.objects.get_or_create(source_id=source_id)
        task.source = source

    task.save()


def __update_handle(db, handle):
    print(f"Updating {handle}...")

    mongo_handle_info = None
    for tries in range(3):
        mongo_handle_info = db['handles'].find_one({
            'judge_id': handle.judge.judge_id.lower(),
            'handle': handle.handle.lower(),
        })
        if mongo_handle_info:
            break

        print(f'Handle info for {handle} not found.')
        print('Redirecting to scraper...')
        scraper_services.scrape_handle_info(db, ":".join([handle.judge.judge_id, handle.handle]))

    if not mongo_handle_info:
        print("ERROR: handle info not found.")
        return

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
            judge_id=judge.judge_id.lower(),
            author_id=user_handle.handle.lower(),
        ))
        # Migrate submission model to SQL model.
        for mongo_submission in mongo_submissions:
            try:
                task = Task.objects.get(
                    judge=judge,
                    task_id__iexact=mongo_submission['task_id'])
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


@shared_task
def update_tasks_info(*tasks):
    db = get_db()
    print(f'update_tasks_info got called with {tasks}')
    for task in tasks:
        try:
            judge_id, task_id = task.split(':', 1)
            task_obj = Task.objects.get(judge__judge_id=judge_id, task_id=task_id)
            __update_task_info(db, task_obj)
        except Exception as e:
            print(f'ERROR: {e}')


@shared_task
def update_all_tasks_info():
    db = get_db()
    print(f'update_all_tasks_info got called')
    for task in Task.objects.all():
        try:
            __update_task_info(db, task)
        except Exception as e:
            print(f'ERROR: {e}')


@shared_task
def update_handles(*handles):
    db = get_db()
    print(f'update_handles got called with {handles}')

    if handles:
        for handle in handles:
            try:
                judge_id, handle_id = handle.split(':', 1)
                handle_obj = UserHandle.objects.get(judge__judge_id=judge_id, handle=handle_id)
                __update_handle(db, handle_obj)
            except Exception as e:
                print(f'ERROR: {e}')


@shared_task
def update_all_handles():
    db = get_db()
    print(f'update_all_handles got called')

    for handle in UserHandle.objects.all():
        __update_handle(db, handle)


@shared_task
def update_users(*usernames):
    db = get_db()
    print(f'update_users got called with {usernames}')

    for username in usernames:
        try:
            user = UserProfile.objects.get(user__username=username)
            __update_user(db, user)
        except Exception as e:
            print(f'ERROR: {e}')


@shared_task
def update_all_users():
    db = get_db()
    print(f'update_all_users got called')
    for user in UserProfile.objects.all():
        __update_user(db, user)