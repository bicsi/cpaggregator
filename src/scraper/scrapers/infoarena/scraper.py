import re
from datetime import datetime

from core.logging import log
from scraper import translators
from scraper.scrapers import Scraper
from scraper.scrapers.infoarena import utils


class InfoarenaScraper(Scraper):
    JUDGE_ID = utils.INFOARENA_JUDGE_ID

    def __init__(self):
        self.default_avatar = utils.get_default_avatar()

    def scrape_submissions_for_user(self, user_id):
        return utils.scrape_submissions(user=user_id)

    def scrape_submissions_for_task(self, task_id):
        return utils.scrape_submissions(task=task_id)

    def scrape_recent_submissions(self):
        return utils.scrape_submissions()

    def scrape_task_info(self, task_id):
        return utils.scrape_task_info(task_id)

    def scrape_user_info(self, handle):
        return utils.scrape_user_info(handle, self.default_avatar)

    def scrape_task_statement(self, task_id):
        statement = utils.scrape_task_statement(task_id)
        statement['statement'] = translators.translate_ro_en(statement['statement'])
        log.debug(statement['statement'])
        return statement

