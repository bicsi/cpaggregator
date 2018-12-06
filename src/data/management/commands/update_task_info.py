import math

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils import timezone
from pymongo import MongoClient

from data import models
from data.models import UserProfile, Submission, Task, Judge, MethodTag
from scraper.database import get_db

DATABASE_NAME = 'competitive'


def _update_task_info(db, task):
    print("Updating {}...".format(task))

    mongo_task_info = db['tasks'].find_one({
        'judge_id': task.judge.judge_id,
        'task_id': task.task_id,
    })
    if mongo_task_info is None:
        print('Task info for {} not found.'.format(task))
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


class Command(BaseCommand):
    help = 'Updates the users with submissions for the available tasks.'

    def handle(self, *args, **options):
        db = get_db()
        for task in Task.objects.all():
            _update_task_info(db, task)
