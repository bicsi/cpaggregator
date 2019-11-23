import argparse

from django.core.management.base import BaseCommand
import datetime

from scraper import services, database


class Command(BaseCommand):
    help = 'Populates the database.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--from_days', type=int, default=0)
        parser.add_argument('--to_days', type=int, default=1)
        parser.add_argument('--tasks', nargs='*')
        parser.add_argument('--users', nargs='*')

    def handle(self, *args, **options):
        if not options['tasks'] and not options['users']:
            print('Please provide tasks or users.')
            return

        if options.get('tasks'):
            services.scrape_submissions_for_tasks(
                *options['tasks'],
                from_days=options['from_days'],
                to_days=options['to_days'],
            )

        if options.get('users'):
            services.scrape_submissions_for_users(
                *options['users'],
                from_days=options['from_days'],
                to_days=options['to_days'],
            )