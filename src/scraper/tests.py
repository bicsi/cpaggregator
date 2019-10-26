from django.test import TestCase

from core.logging import log
from scraper.scrapers.codeforces.utils import *
# Create your tests here.


log.error(scrape_task_info("1209_e2"))
log.error(scrape_task_statement("1251_a"))