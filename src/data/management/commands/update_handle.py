import math

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils import timezone
from pymongo import MongoClient

from data import models
from data.models import UserProfile, Submission, Task, Judge, MethodTag, UserHandle
from scraper.database import get_db

DATABASE_NAME = 'competitive'


def _update_handle(db, handle):
    if handle.judge_id == 'cf':
        print(f'SKIPPING {handle}; only cf supported.')
        return

    print(f"Updating {handle}...")

    mongo_handle_info = db['handles'].find_one({
        'judge_id': handle.judge.judge_id,
        'handle': handle.handle,
    })
    if mongo_handle_info is None:
        print(f'Handle info for {handle} not found.')
        return

    if 'photo_url' in mongo_handle_info:
        handle.photo_url = mongo_handle_info['photo_url']

    handle.save()


class Command(BaseCommand):
    help = 'Updates the handles with scraped info.'

    def handle(self, *args, **options):
        db = get_db()
        for handle in UserHandle.objects.all():
            _update_handle(db, handle)
