from data.models import Task
from scraper import utils
from scraper.scrapers.infoarena import utils as infoarena_scraper
from scraper.scrapers.csacademy import utils as csacademy_scraper


def scrape_submissions_for_task(db, task, from_date, to_date):
    print('Scraping submissions for task: %s...' % task)
    judge_id, task_id = task.split(':')

    if judge_id == 'ia':
        if task_id == '*':
            submissions = infoarena_scraper.scrape_submissions()
            all_task_ids = [task.task_id for task in Task.objects.filter(judge__judge_id=judge_id)]
            print("All task ids: ", all_task_ids)
            submissions = filter(lambda s: s['task_id'] in all_task_ids, submissions)
        else:
            submissions = infoarena_scraper.scrape_submissions(task=task_id)

    elif judge_id == 'csa':
        if task_id == '*':
            all_task_ids = [task.task_id for task in Task.objects.filter(judge__judge_id=judge_id)]
            print("All task ids: ", all_task_ids)
            submissions = csacademy_scraper.scrape_submissions_for_tasks(all_task_ids)
        else:
            submissions = csacademy_scraper.scrape_submissions_for_tasks([task_id])

    else:
        print("Judge id not recognized: %s" % judge_id)
        return

    submissions_to_write = []
    for submission in submissions:
        if submission['submitted_on'] < to_date:
            break
        submissions_to_write.append(submission)

    utils.write_submissions(db, submissions_to_write, chunk_size=1000000)

