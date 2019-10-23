from scraper.scrapers import Scraper
from . import utils


class OjuzScraper(Scraper):
    JUDGE_ID = utils.OJUZ_JUDGE_ID

    def scrape_submissions_for_user(self, user_id):
        return utils.scrape_submissions(user=user_id)

    def scrape_submissions_for_task(self, task_id):
        return utils.scrape_submissions(problem=task_id)

    def scrape_recent_submissions(self):
        return utils.scrape_submissions()

