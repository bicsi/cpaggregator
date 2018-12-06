import heapq
from datetime import datetime, timedelta
from itertools import takewhile

from data.models import Task
from scraper import utils
from scraper.scrapers.infoarena import utils as infoarena_scraper
from scraper.scrapers.csacademy import utils as csacademy_scraper
from scraper.scrapers.codeforces import utils as codeforces_scraper


def __expand_task(judge_id, task_id):
    task_ids = [task_id]
    if task_id == '*':
        task_ids = [task.task_id for task in
                    Task.objects.filter(judge__judge_id=judge_id)]
    print('Task ids:', task_ids)
    return task_ids


def scrape_submissions_for_task(db, task, from_date, to_date):
    print('Scraping submissions for task: %s...' % task)
    judge_id, task_id = task.split(':', 1)
    task_ids = __expand_task(judge_id, task_id)

    if judge_id == 'ia':
        if len(task_ids) == 1:
            submissions = infoarena_scraper.scrape_submissions(task=task_ids[0])
        else:
            if to_date > datetime.now() - timedelta(days=100):
                submissions = filter(lambda sub: sub['task_id'] in task_ids, infoarena_scraper.scrape_submissions())
            else:
                all_submissions = [infoarena_scraper.scrape_submissions(task=task_id) for task_id in task_ids]
                submissions = heapq.merge(*all_submissions, key=lambda x: x['submitted_on'], reverse=True)

    elif judge_id == 'csa':
        submissions = csacademy_scraper.scrape_submissions_for_tasks(task_ids)

    elif judge_id == 'cf':
        submissions = codeforces_scraper.scrape_submissions_for_tasks(task_ids)

    else:
        print("Judge id not recognized: %s" % judge_id)
        return

    submissions_to_write = takewhile(lambda x: x['submitted_on'] >= to_date, submissions)
    utils.write_submissions(db, submissions_to_write, chunk_size=1000)


def scrape_task_info(db, task):
    print('Scraping task {} info...'.format(task))
    judge_id, task_id = task.split(':', 1)
    task_ids = __expand_task(judge_id, task_id)

    if judge_id == 'ia':
        task_infos = [infoarena_scraper.scrape_task_info(task_id)
                      for task_id in task_ids]

    elif judge_id == 'csa':
        task_infos = csacademy_scraper.scrape_task_info(task_ids)

    elif judge_id == 'cf':
        task_infos = codeforces_scraper.scrape_task_info(task_ids)

    else:
        print("Judge id not recognized: %s" % judge_id)
        return

    utils.write_tasks(db, task_infos)


