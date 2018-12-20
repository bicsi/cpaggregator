from django.core.management.base import BaseCommand

from data import services
from data.models import UserHandle


class Command(BaseCommand):
    help = 'Updates the handles with scraped info.'

    def handle(self, *args, **options):
        services.update_handles(UserHandle.objects.all())
