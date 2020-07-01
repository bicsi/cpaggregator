from scraper.scrapers import Scraper
from . import utils


class TimusScraper(Scraper):
    JUDGE_ID = utils.TIMUS_JUDGE_ID

    def scrape_submissions_for_user(self, user_id):
        return utils.scrape_submissions(author=user_id)

    def scrape_submissions_for_task(self, task_id):
        return utils.scrape_submissions(num=task_id)

    def scrape_recent_submissions(self):
        return utils.scrape_submissions()

    def scrape_task_info(self, task_id):
        return utils.scrape_task_info(task_id)
