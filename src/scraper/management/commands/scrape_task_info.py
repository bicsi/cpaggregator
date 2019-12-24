import argparse

from django.core.management.base import BaseCommand
from scraper import services, database


class Command(BaseCommand):
    help = 'Populates the database.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--tasks', nargs='+')

    def handle(self, *args, **options):
        db = database.get_db()
        for task in options['tasks']:
            services.scrape_task_info(db, task)
