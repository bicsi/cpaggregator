import argparse

from django.core.management.base import BaseCommand
from scraper import services, database


class Command(BaseCommand):
    help = 'Populates the database.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--tasks', nargs='+')

    def handle(self, *args, **options):
        db = database.get_db()
        tasks = options['tasks']
        print("TASKS", tasks)

        for task in tasks:
            services.scrape_task_info(db, task)