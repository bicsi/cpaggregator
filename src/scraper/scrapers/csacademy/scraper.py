from core.logging import log
from scraper.scrapers import Scraper
from . import utils


class CSAcademyScraper(Scraper):
    JUDGE_ID = utils.CSACADEMY_JUDGE_ID

    def __init__(self):
        self.csrf_token = utils.get_csrf_token()
        self.task_name_dict = utils.get_task_name_dict(self.csrf_token)
        self.all_task_info = None

    def scrape_submissions_for_task(self, task_id):
        # CSAcademy has their own task ids that are numerical and are kept inside
        # a global map. We keep `task_id` as a parameter for consistency.
        return utils.scrape_submissions_for_task(
            self.csrf_token, task_id, self.task_name_dict)

    def scrape_task_info(self, task_id):
        # Compute if not added to cache.
        if not self.all_task_info:
            self.all_task_info = utils.scrape_all_task_info(self.csrf_token)

        for task_info in self.all_task_info:
            if task_info['task_id'] == task_id.lower():
                return task_info

        raise Exception(
            f"Task '{task_id}' not found in task_info", self.all_task_info)
