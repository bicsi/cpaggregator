from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    if created:
        task_id = ":".join([instance.judge.judge_id, instance.task_id])

        print(f'Created new task {task_id}: updating info async...')
        services.update_tasks_info.si(task_id).apply_async()
        print('Scraping submissions and updating users async...')
        celery.chain(
            services.scraper_services.scrape_submissions_for_tasks.si(task_id),
            services.update_all_users.si(),
        ).apply_async()

"""
    Handle signals.
"""


@receiver(post_save, sender=UserHandle)
def create_handle(sender, instance, created, **kwargs):
    if created:
        print('Created new handle: updating info...')
        celery.chain(
            services.update_handles.si(':'.join([instance.judge.judge_id, instance.handle])),
            services.update_users.si(instance.user.user.username),
        ).apply_async()


