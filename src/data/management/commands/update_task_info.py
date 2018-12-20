from django.core.management.base import BaseCommand

from data import services
from data.models import Task


class Command(BaseCommand):
    help = 'Updates the users with submissions for the available tasks.'

    def handle(self, *args, **options):
        services.update_tasks_info(Task.objects.all())
