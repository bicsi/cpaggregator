from django.core.management.base import BaseCommand

from data.models import Task
from stats import services


class Command(BaseCommand):
    help = 'Recomputes statistics for tasks.'

    def handle(self, *args, **options):
        for task in Task.objects.all():
            print(f'Computing statistics for {task}...')
            services.compute_task_statistics(task)