from django.core.management.base import BaseCommand

from data.models import Task
from stats import services


class Command(BaseCommand):
    help = 'Recomputes statistics for users.'

    def handle(self, *args, **options):
        services.compute_user_statistics()