import argparse
import os

from django.core.management.base import BaseCommand
import csv

from cpaggregator.settings import BASE_DIR
from data.models import Task
from data.populate import create_judge, create_user, create_user_handle, create_task
from scraper.database import get_db
from scraper.services import scrape_submissions_for_task

ASD_USERS_CSV_PATH = os.path.join(os.path.dirname(BASE_DIR), "data", "management", "files", "asd_users.csv")
ASD_TASKS_CSV_PATH = os.path.join(os.path.dirname(BASE_DIR), "data", "management", "files", "asd_tasks.csv")


def _create_judges():
    create_judge(
        judge_id='ac',
        name='AtCoder',
        homepage='https://www.atcoder.jp/',
    )
    create_judge(
        judge_id='ia',
        name='Infoarena',
        homepage='https://www.infoarena.ro/',
    )
    create_judge(
        judge_id='poj',
        name='POJ',
        homepage='http://poj.org/',
    )
    create_judge(
        judge_id='csa',
        name='CSAcademy',
        homepage='http://www.csacademy.com/',
    )
    create_judge(
        judge_id='cf',
        name='Codeforces',
        homepage='https://codeforces.com/',
    )


def _create_tasks():
    # Seminar ASD.
    with open(ASD_TASKS_CSV_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            create_task(task_id=row['Task Id'])


def _create_users():
    # Seminar ASD.
    with open(ASD_USERS_CSV_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            names = row['Nume & Prenume'].split()
            first_names = names[1:]
            last_name = names[0]
            username = "".join(first_names) + last_name
            # Create user in database.
            create_user(
                username=username,
                first_name="-".join(first_names),
                last_name=last_name
            )

            # Link infoarena username.
            if row.get('Handle infoarena', "") != "":
                create_user_handle(
                    username=username,
                    judge_id='ia',
                    handle=row['Handle infoarena'],
                )

            # Link csacademy username.
            if row.get('Handle CSAcademy', "") != "":
                create_user_handle(
                    username=username,
                    judge_id='csa',
                    handle=row['Handle CSAcademy'],
                )


class Command(BaseCommand):
    help = 'Populates the database.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('days', type=int, default=1)
        parser.add_argument('tasks', nargs='*')

    def handle(self, *args, **options):
        _create_judges()
        _create_tasks()
        _create_users()
