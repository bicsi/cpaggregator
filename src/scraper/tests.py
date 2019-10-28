from django.test import TestCase

# Create your tests here.

from scraper.services import scrape_submissions_for_users

scrape_submissions_for_users('cf:*')
