from scraper import utils
from scraper.scrapers.infoarena import utils as infoarena_scraper


def scrape_submissions_for_task(db, task):
    print('Scraping submissions for task: %s...' % task)
    judge_id, task_id = task.split(':')
    submissions = []

    if judge_id == 'ia':
        submissions = infoarena_scraper.scrape_submissions(task=task_id)
    elif judge_id == 'csa':
        pass
        # submissions = .scrape_submissions_for_task(task_id)
    else:
        print("Judge id not recognized: %s" % judge_id)
        return
    utils.write_submissions(db, submissions, chunk_size=1000)

