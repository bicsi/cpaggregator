from scraper import utils
from scraper.scrapers.infoarena import utils as infoarena_scraper
from scraper.scrapers.csacademy import utils as csacademy_scraper


def scrape_submissions_for_task(db, task, from_date, to_date):
    print('Scraping submissions for task: %s...' % task)
    judge_id, task_id = task.split(':')

    if judge_id == 'ia':
        submissions = infoarena_scraper.scrape_submissions(task=task_id)
    elif judge_id == 'csa':
        pass
        submissions = csacademy_scraper.scrape_submissions_for_task(task_id, from_date=from_date)
    else:
        print("Judge id not recognized: %s" % judge_id)
        return

    submissions_to_write = []
    for submission in submissions:
        if submission['submitted_on'] < to_date:
            break
        submissions_to_write.append(submission)

    utils.write_submissions(db, submissions_to_write, chunk_size=1000000)

