import argparse

from django.core.management.base import BaseCommand

from data import services
from data.models import Task


class Command(BaseCommand):
    help = 'Updates the users with submissions for the available tasks.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--tasks', nargs='*')

    def handle(self, *args, **options):
        if options['tasks']:
            services.update_tasks_info(*options['tasks'])
        else:
            services.update_all_tasks_info()
