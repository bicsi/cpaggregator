import math
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.text import slugify

from core.logging import log
from data.models import MethodTag, Task, Submission, UserProfile, UserHandle, TaskSource, JudgeTaskStatistic, \
    TaskStatement
from scraper.database import get_db
import scraper.services as scraper_services

from celery import shared_task


@shared_task
def update_all_users():
    log.info(f'Updating all users profile picture...')

    # Photo urls.
    judge_priority = {'cf': 3, 'ia': 2, 'csa': 1}
    handles = list(UserHandle.objects
                   .filter(judge__judge_id__in=judge_priority.keys())
                   .select_related('user', 'judge'))
    handles.sort(key=lambda h: judge_priority[h.judge.judge_id], reverse=True)
    computed_users = set()
    users_to_update = []
    for handle in handles:
        if not handle.photo_url or handle.user in computed_users:
            continue
        computed_users.add(handle.user)
        if handle.photo_url != handle.user.avatar_url:
            handle.user.avatar_url = handle.photo_url
            users_to_update.append(handle.user)

    UserProfile.objects.bulk_update(users_to_update, ['avatar_url'])
    log.success(f"{len(users_to_update)} users updated.")
