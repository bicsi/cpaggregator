import argparse

from django.core.management.base import BaseCommand
from schedule import scheduler


class Command(BaseCommand):
    help = 'Start scheduler.'

    def handle(self, *args, **options):
        scheduler.start()
