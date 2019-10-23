from scraper.scrapers import Scraper
from . import utils


class AtCoderScraper(Scraper):
    JUDGE_ID = utils.ATCODER_JUDGE_ID

    def scrape_submissions_for_task(self, task_id):
        return utils.scrape_submissions_for_task(task_id)

    def scrape_task_info(self, task_id):
        return utils.scrape_task_info(task_id)
