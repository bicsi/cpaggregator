import heapq
from datetime import datetime, timedelta
from itertools import takewhile

from data.models import Task, UserHandle
from scraper import utils, database
from scraper.scrapers.infoarena import utils as infoarena_scraper
from scraper.scrapers.csacademy import utils as csacademy_scraper
from scraper.scrapers.codeforces import utils as codeforces_scraper
from scraper.scrapers.atcoder import utils as atcoder_scraper
from scraper.scrapers.ojuz import utils as ojuz_scraper

from celery import shared_task


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
    print('Handles:', handles)
    return handles


def __scrape_submissions_for_tasks(db, judge_id, task_ids, from_date, to_date):
    # Infoarena - special logic to optimize monitor.
    if judge_id == 'ia':
        if len(task_ids) == 1:
            submissions = infoarena_scraper.scrape_submissions(task=task_ids[0])
        else:
            if to_date > datetime.now() - timedelta(days=100):
                submissions = filter(lambda sub: sub['task_id'] in task_ids, infoarena_scraper.scrape_submissions())
            else:
                all_submissions = [infoarena_scraper.scrape_submissions(task=task_id) for task_id in task_ids]
                submissions = heapq.merge(*all_submissions, key=lambda x: x['submitted_on'], reverse=True)

    # oj.uz - same as infoarena.
    elif judge_id == 'ojuz':
        if len(task_ids) == 1:
            submissions = ojuz_scraper.scrape_submissions(problem=task_ids[0])
        else:
            if to_date > datetime.now() - timedelta(days=100):
                submissions = filter(lambda sub: sub['task_id'] in task_ids, ojuz_scraper.scrape_submissions())
            else:
                all_submissions = [ojuz_scraper.scrape_submissions(problem=task_id) for task_id in task_ids]
                submissions = heapq.merge(*all_submissions, key=lambda x: x['submitted_on'], reverse=True)

    elif judge_id == 'csa':
        submissions = csacademy_scraper.scrape_submissions_for_tasks(task_ids)

    elif judge_id == 'cf':
        submissions = codeforces_scraper.scrape_submissions_for_tasks(task_ids)

    elif judge_id == 'ac':
        submissions = atcoder_scraper.scrape_submissions_for_tasks(task_ids)
        for idx, submission in enumerate(submissions):
            print(submission)
            if idx > 10:
                break
    else:
        print(f"Judge id not recognized: {judge_id}")
        return

    submissions_to_write = takewhile(lambda x: x['submitted_on'] >= to_date, submissions)
    utils.write_submissions(db, submissions_to_write, chunk_size=1000)


@shared_task
def scrape_submissions_for_tasks(*tasks, from_days=0, to_days=100000):
    db = database.get_db()

    print("TASKS", tasks)

    from_date = datetime.now() - timedelta(days=from_days)
    to_date = datetime.now() - timedelta(days=to_days)

    print('Scraping submissions between:')
    print(to_date)
    print(from_date)

    task_dict = {}
    for task in tasks:
        judge_id, task_id = task.split(':', 1)
        task_ids = __expand_task(judge_id, task_id)
        task_dict[judge_id] = task_dict.get(judge_id, []) + task_ids

    for judge_id, task_ids in task_dict.items():
        print(f'Scraping task submissions from judge {judge_id}:')
        print(task_ids)
        __scrape_submissions_for_tasks(db, judge_id, list(set(task_ids)), from_date, to_date)


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

    elif judge_id == 'ojuz':
        task_infos = [ojuz_scraper.scrape_task_info(task_id)
                      for task_id in task_ids]

    elif judge_id == 'ac':
        task_infos = atcoder_scraper.scrape_task_info(task_ids)

    else:
        print("Judge id not recognized: %s" % judge_id)
        return

    utils.write_tasks(db, task_infos)


def scrape_handle_info(db, handle):
    print('Scraping handle {} info...'.format(handle))
    judge_id, handle_id = handle.split(':', 1)
    handles = __expand_handle(judge_id, handle_id)

    if judge_id == 'cf':
        handle_infos = codeforces_scraper.scrape_user_info(handles)
    elif judge_id == 'ia':
        handle_infos = infoarena_scraper.scrape_user_info(handles)
    else:
        print("Judge id not recognized: %s" % judge_id)
        return

    utils.write_handles(db, handle_infos)


@shared_task
def scrape_tasks_info():
    db = database.get_db()
    for task in Task.objects.all():
        try:
            scrape_task_info(db, ':'.join([task.judge.judge_id, task.task_id]))
        except Exception as e:
            print(f'ERROR: Could not parse task: {task}. {e}')


@shared_task
def scrape_handles_info():
    db = database.get_db()
    for handle in UserHandle.objects.all():
        try:
            scrape_handle_info(db, ':'.join([handle.judge.judge_id, handle.handle]))
        except Exception as e:
            print(f'ERROR: Could not parse handle: {handle}. {e}')

