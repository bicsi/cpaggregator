import time
import urllib
from datetime import datetime
import requests

from core.logging import log
from scraper import database


def split_into_chunks(iterable, chunk_size):
    buffer = []
    for elem in iterable:
        buffer.append(elem)
        if len(buffer) == chunk_size:
            yield buffer
            buffer = []

    if len(buffer) > 0:
        yield buffer


def get_page(page_url, max_retries=10, **query_dict):
    """
    Sends a GET request, while also printing the page to console.
    :param max_retries: the maximum number of retries
    :param page_url: the url of the GET request
    :param query_dict: the GET query parameters
    :return: the page received
    """
    if len(query_dict) > 0:
        query_string = urllib.parse.urlencode(query_dict)
        page_url += "?" + query_string

    page = None
    for tries in range(max_retries):
        log.debug(f"GET: {page_url}")
        page = requests.get(page_url)
        if page.status_code == 200 or page.status_code == 400 or page.status_code == 404:
            break
        else:
            log.warning(f'Request failed (status code: {page.status_code}). Sleeping for 2 seconds...')
            time.sleep(2)
            log.info('Retrying...')

    if not page:
        log.error("Request failed. Page not found.")
    if page.status_code != 200:
        log.error("Request failed. Status code: %d" % page.status_code)

    return page


def write_submissions(db, submissions, chunk_size=100):
    """
    Writes a list of submissions to database.
    :param db: Database instance.
    :param chunk_size: how many submissions to be written at once
    :param submissions: list/generator of submissions
    :return: the number of submissions inserted
    """
    total_inserted = 0
    for chunk in split_into_chunks(submissions, chunk_size):
        log.info(f"Writing chunk of size {len(chunk)} to database...")
        
        num_inserted = database.insert_submissions(db, chunk)
        log.info(f"{num_inserted} submissions written to database.")
        total_inserted += num_inserted
    return total_inserted


def write_tasks(db, tasks, chunk_size=3):
    """
    Writes a list of tasks to database.
    :param db: Database instance.
    :param chunk_size: how many tasks to be written at once
    :param tasks: list/generator of tasks
    :return: the number of tasks inserted
    """
    total_inserted = 0
    for chunk in split_into_chunks(tasks, chunk_size):
        log.info("Writing chunk to database...")
        num_inserted = database.insert_tasks(db, chunk)
        log.info(f"{num_inserted} tasks written to database.")
        total_inserted += num_inserted
    return total_inserted


def write_handles(db, handles, chunk_size=100):
    """
    Writes a list of tasks to database.
    :param db: Database instance.
    :param chunk_size: how many tasks to be written at once
    :param handles: list/generator of handle info
    :return: the number of tasks inserted
    """
    total_inserted = 0
    for chunk in split_into_chunks(handles, chunk_size):
        log.info("Writing chunk to database...")
        num_inserted = database.insert_handles(db, chunk)
        log.info(f"{num_inserted} handles written to database.")
        total_inserted += num_inserted
    return total_inserted


def write_report(db, report_id, report, created_at=datetime.utcnow()):
    """
    Writes a report to database.
    :param db: Database instance.
    :param report_id: a unique identifier to the report
    :param report: the report object (dict)
    :param created_at: the date created
    """
    database.insert_report(db, report_id, created_at, report)
