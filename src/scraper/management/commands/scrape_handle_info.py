import argparse

from django.core.management.base import BaseCommand
from scraper import services, database


class Command(BaseCommand):
    help = 'Populates the database.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--handles', nargs='+')

    def handle(self, *args, **options):
        handles = options['handles']
        print("HANDLES", handles)

        for handle in handles:
            services.scrape_handle_info(handle)
