from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from data import services
from data.models import UserProfile, Task, UserHandle

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
        print('Created new task: updating info...')
        services.update_tasks_info([instance])


"""
    Handle signals.
"""


@receiver(post_save, sender=UserHandle)
def create_task(sender, instance, created, **kwargs):
    if created:
        print('Created new handle: updating info...')
        services.update_handles([instance])
        services.update_users([instance.user])


