from django.test import TestCase

# Create your tests here.
from search.queries import search_task
from core.logging import log

log.info(search_task("Round 352"))