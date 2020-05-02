from django.test import TestCase

# Create your tests here.
from scraper.scrapers.csacademy.scraper import CSAcademyScraper
from scraper.scrapers.infoarena.scraper import InfoarenaScraper
from scraper.services import scrape_submissions_for_users


class CSAScraperTestCase(TestCase):
    def test_csa_scraper(self):
        total = 0
        last_id = None
        for submission in CSAcademyScraper().scrape_submissions_for_task("closest-pair"):
            if last_id is not None:
                assert int(last_id) > int(submission['submission_id'])
            last_id = submission['submission_id']
            if total > 5:
                break
            total += 1

class IATC(TestCase):
    def test_tz(self):
        for submission in InfoarenaScraper().scrape_recent_submissions():
            print(submission['submitted_on'])
            break