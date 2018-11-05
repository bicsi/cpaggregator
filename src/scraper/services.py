import heapq
from datetime import datetime, timedelta

from data.models import Task
from scraper import utils
from scraper.scrapers.infoarena import utils as infoarena_scraper
from scraper.scrapers.csacademy import utils as csacademy_scraper
from scraper.scrapers.codeforces import utils as codeforces_scraper


def scrape_submissions_for_task(db, task, from_date, to_date):
    print('Scraping submissions for task: %s...' % task)
    judge_id, task_id = task.split(':')

    task_ids = [task_id]
    if task_id == '*':
        task_ids = [task.task_id for task in Task.objects.filter(judge__judge_id=judge_id)]
    print('Task ids:', task_ids)

    if judge_id == 'ia':
        if len(task_ids) == 1:
            submissions = infoarena_scraper.scrape_submissions(task=task_ids[0])
        else:
            if to_date > datetime.now() - timedelta(days=100):
                submissions = infoarena_scraper.scrape_submissions()
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

    submissions_to_write = []
    for submission in submissions:
        if submission['submitted_on'] < to_date:
            break
        submissions_to_write.append(submission)

    utils.write_submissions(db, submissions_to_write, chunk_size=1000000)

