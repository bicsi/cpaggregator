import argparse

from django.core.management.base import BaseCommand
import datetime

from data.models import Task
from scraper.database import get_db
from scraper.services import scrape_submissions_for_task


class Command(BaseCommand):
    help = 'Populates the database.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--from_days', type=int, default=0)
        parser.add_argument('--to_days', type=int, default=1)
        parser.add_argument('--tasks', nargs='*')

    def handle(self, *args, **options):
        db = get_db()
        tasks = options['tasks']
        from_date = datetime.datetime.now() - datetime.timedelta(days=options['from_days'])
        to_date = datetime.datetime.now() - datetime.timedelta(days=options['to_days'])
        print('Scraping submissions between:')
        print(to_date)
        print(from_date)

        if tasks:
            for task in tasks:
                scrape_submissions_for_task(db, task, from_date, to_date)
        else:
            for task in Task.objects.all():
                task_id = ":".join([task.judge.judge_id, task.task_id])
                scrape_submissions_for_task(db, task_id, from_date, to_date)
