from scraper import utils
from scraper.scrapers.infoarena import utils as infoarena_scraper
from scraper.scrapers.csacademy import utils as csacademy_scraper


def scrape_submissions_for_task(db, task, date_from):
    print('Scraping submissions for task: %s...' % task)
    judge_id, task_id = task.split(':')
    submissions = []

    if judge_id == 'ia':
        submissions = infoarena_scraper.scrape_submissions(task=task_id)
    elif judge_id == 'csa':
        pass
        submissions = csacademy_scraper.scrape_submissions_for_task(task_id)
    else:
        print("Judge id not recognized: %s" % judge_id)
        return

    submissions_to_write = []
    for submission in submissions:
        if submission['submitted_on'] < date_from:
            break
        submissions_to_write.append(submission)

    utils.write_submissions(db, submissions_to_write, chunk_size=1000000)

