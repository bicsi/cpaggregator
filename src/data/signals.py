from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.logging import log
from cpaggregator import settings
from data import services
from data.models import UserProfile, Task, UserHandle

import celery

"""
    User and UserProfile signals.
"""


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            first_name=instance.first_name,
            last_name=instance.last_name)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile') and instance.profile is not None:
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance, username=instance.username)


"""
    Task signals.
"""


@receiver(post_save, sender=Task)
def create_task(sender, instance, created, **kwargs):
    if created and settings.USE_CELERY:
        task_path = instance.get_path()
        log.info(f'Created new task {task_path}: updating info async...')
        services.scraper_services.scrape_task_info.si(task_path).apply_async()
        log.info('Scraping submissions and updating users async...')
        services.scraper_services.scrape_submissions_for_tasks.si(task_path).apply_async()

"""
    Handle signals.
"""


@receiver(post_save, sender=UserHandle)
def create_handle(sender, instance, created, **kwargs):
    if created and settings.USE_CELERY:
        log.info('Created new handle: updating info...')
        handle = '/'.join([instance.judge.judge_id, instance.handle])
        services.scraper_services.scrape_handle_info.si(handle).apply_async()
        services.scraper_services.scrape_submissions_for_users.si(handle).apply_async()


