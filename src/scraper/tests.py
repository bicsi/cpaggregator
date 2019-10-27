from django.test import TestCase

# Create your tests here.

from scraper.services import scrape_submissions_for_tasks

for submission in scrape_submissions_for_tasks('ac:*'):
    print(submission)
