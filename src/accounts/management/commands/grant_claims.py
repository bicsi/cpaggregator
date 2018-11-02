import argparse
import os

from django.core.management.base import BaseCommand
import csv

from accounts.models import UserProfileClaim
from cpaggregator.settings import BASE_DIR
from data.models import Task
from data.populate import create_judge, create_user, create_user_handle, create_task
from scraper.database import get_db
from scraper.services import scrape_submissions_for_task


class Command(BaseCommand):
    help = 'Grants claims.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--ids', nargs='+')

    def handle(self, *args, **options):
        for claim_id in options['ids']:
            claim = UserProfileClaim.objects.get(id=int(claim_id))
            claim.solve()
