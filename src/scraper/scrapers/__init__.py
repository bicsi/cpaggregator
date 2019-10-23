from core.logging import log
from .scraper import Scraper
from .infoarena.scraper import InfoarenaScraper
from .codeforces.scraper import CodeforcesScraper
from .csacademy.scraper import CSAcademyScraper
from .atcoder.scraper import AtCoderScraper
from .ojuz.scraper import OjuzScraper

__SUBMISSION_SCRAPERS__ = [
    InfoarenaScraper,
    CodeforcesScraper,
    CSAcademyScraper,
    AtCoderScraper,
    OjuzScraper,
]


def create_scraper(judge_id: str) -> Scraper:
    for scraper_kls in __SUBMISSION_SCRAPERS__:
        if scraper_kls.JUDGE_ID == judge_id:
            log.debug(f"Found scraper for judge '{judge_id}': {scraper_kls.__name__}")
            return scraper_kls()
    raise Exception(f"No scraper configured for {judge_id}.")