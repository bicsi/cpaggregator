from django.test import TestCase

from core.logging import log
# Create your tests here.
from scraper.translators import translate_ro_en
from scraper.scrapers.infoarena.utils import scrape_task_statement

task_statement_ro = scrape_task_statement("rutier")
log.error(task_statement_ro)
task_statement_en = translate_ro_en(task_statement_ro)
log.error(task_statement_en)