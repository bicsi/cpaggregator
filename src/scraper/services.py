import heapq
import itertools
from datetime import datetime, timedelta

from celery import shared_task

from core.logging import log
from data.models import Task, UserHandle
from scraper import utils, database, scrapers


def __expand_task(judge_id, task_id):
    task_ids = [task_id]
    if task_id == '*':
        task_ids = [task.task_id for task in
                    Task.objects.filter(judge__judge_id=judge_id)]
    return task_ids


def __expand_handle(judge_id, handle):
    handles = [handle]
    if handle == '*':
        handles = [handle.handle for handle in
                   UserHandle.objects.filter(judge__judge_id=judge_id)]
    log.info(f'Handles: {handles}')
    return handles


def __scrape_submissions_for_tasks(db, judge_id, task_ids, from_date, to_date):
    scraper = scrapers.create_scraper(judge_id)

    # Get submissions as list of generators.
    submissions = []
    for task_id in task_ids:
        try:
            subs = scraper.scrape_submissions_for_task(task_id)
            submissions.append(subs)
        except NotImplementedError:
            log.warning(f'Scraping submissions not implemented for {scraper.__class__.__name__}.')
            return
        except Exception as ex:
            log.exception(ex)

    # Merge the generators into one and take while submitted on is good
    submissions = heapq.merge(*submissions, key=lambda x: x['submitted_on'], reverse=True)
    submissions = itertools.takewhile(lambda x: x['submitted_on'] >= to_date, submissions)

    # Write the submissions to DB.
    utils.write_submissions(db, submissions, chunk_size=1000)


@shared_task
def scrape_submissions_for_tasks(*tasks, from_days=0, to_days=100000):
    db = database.get_db()

    log.info(f"Scraping submissions for tasks {tasks}...")

    from_date = datetime.now() - timedelta(days=from_days)
    to_date = datetime.now() - timedelta(days=to_days)

    log.info(f'Dates between {to_date} and {from_date}...')

    task_dict = {}
    for task in tasks:
        judge_id, task_id = task.split(':', 1)
        task_ids = __expand_task(judge_id, task_id)
        task_dict[judge_id] = task_dict.get(judge_id, []) + task_ids

    for judge_id, task_ids in task_dict.items():
        log.info(f"Scraping task submissions from judge '{judge_id}':")
        log.info(f'Task ids: {task_ids}')
        __scrape_submissions_for_tasks(db, judge_id, list(set(task_ids)), from_date, to_date)


def scrape_task_info(db, task):
    log.info(f"Scraping task info for task '{task}'...")
    judge_id, task_id = task.split(':', 1)
    task_ids = __expand_task(judge_id, task_id)

    scraper = scrapers.create_scraper(judge_id)
    task_infos = []
    log.info(f"Task ids: {task_ids}")

    for task_id in task_ids:
        try:
            task_info = scraper.scrape_task_info(task_id)
            if task_info is None:
                log.warning(f"Did not find task info for '{task_id}'. Skipping...")
                continue

            log.debug(task_info)
            log.info(f"Successfully scraped '{task_id}' [{task_info['title']}]...")
            task_infos.append(task_info)
        except NotImplementedError:
            log.warning(f'Scraping tasks not implemented for {scraper.__class__.__name__}.')
            return
        except Exception as ex:
            log.exception(ex)

    utils.write_tasks(db, task_infos)


def scrape_handle_info(db, handle):
    log.info(f"Scraping info for handle '{handle}'...")
    judge_id, handle_id = handle.split(':', 1)
    handles = __expand_handle(judge_id, handle_id)
    log.info(f"Handles: {handles}")

    scraper = scrapers.create_scraper(judge_id)

    user_infos = []
    for handle in handles:
        try:
            user_info = scraper.scrape_user_info(handle)
            log.info(f"Successfully scraped user info for '{handle}'")
            log.debug(user_info)
            user_infos.append(user_info)
        except NotImplementedError:
            log.warning(f'Scraping handles not implemented for {scraper.__class__.__name__}.')
            return
        except Exception as ex:
            log.exception(ex)

    utils.write_handles(db, user_infos)


@shared_task
def scrape_tasks_info():
    db = database.get_db()
    for task in Task.objects.all():
        try:
            scrape_task_info(db, ':'.join([task.judge.judge_id, task.task_id]))
        except Exception as e:
            log.exception(f"Could not parse task '{task}': {e}")


@shared_task
def scrape_handles_info():
    db = database.get_db()
    for handle in UserHandle.objects.all():
        try:
            scrape_handle_info(db, ':'.join([handle.judge.judge_id, handle.handle]))
        except Exception as e:
            log.exception(f"Could not parse handle '{handle}': {e}")
