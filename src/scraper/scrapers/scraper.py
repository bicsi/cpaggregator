from collections import Generator
from typing import Dict


class Scraper:
    def scrape_submissions_for_user(self, user_id: str) -> Generator:
        raise NotImplementedError()

    def scrape_submissions_for_task(self, task_id: str) -> Generator:
        raise NotImplementedError()

    def scrape_recent_submissions(self) -> Generator:
        raise NotImplementedError()

    def scrape_task_info(self, task_id: str) -> Dict:
        raise NotImplementedError()

    def scrape_user_info(self, handle: str) -> Dict:
        raise NotImplementedError()
