from scraper.scrapers import Scraper
from . import utils


class CodeforcesScraper(Scraper):
    JUDGE_ID = utils.CODEFORCES_JUDGE_ID

    def scrape_submissions_for_task(self, task_id):
        return utils.scrape_submissions_for_task(task_id)

    def scrape_task_info(self, task_id):
        return utils.scrape_task_info(task_id)

    def scrape_user_info(self, handle: str):
        # Codeforces has support for multiple handles.
        result = utils.scrape_user_info([handle])
        if len(result) > 1:
            raise Exception(f"Multiple users with '{handle}'", result)

        return None if len(result) == 0 else result[0]

    def scrape_task_statement(self, task_id):
        return utils.scrape_task_statement(task_id)
