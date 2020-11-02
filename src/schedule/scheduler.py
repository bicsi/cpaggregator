from apscheduler.schedulers.blocking import BlockingScheduler
from core.logging import log
from scraper import services as scraper_services
from stats import services as stats_services
from . import services

job_defaults = {
    'coalesce': False,
    'max_instances': 2,
}
scheduler = BlockingScheduler(job_defaults=job_defaults)


@scheduler.scheduled_job('interval', seconds=30)
def scrape_recent_submissions():
    for judge_id in ['ia', 'cf']:
        scraper_services.scrape_recent_submissions(judge_id)


@scheduler.scheduled_job('interval', seconds=10)
def scrape_user_info_ten_days_ago():
    services.scrape_user_info(to_days=10, batch_size=5)


@scheduler.scheduled_job('interval', minutes=30)
def scrape_user_info_all_time():
    services.scrape_user_info(to_days=10, batch_size=15)


@scheduler.scheduled_job('interval', seconds=10)
def scrape_task_submissions_last_days():
    services.scrape_task_submissions(to_days=5, batch_size=10)


@scheduler.scheduled_job('interval', minutes=30)
def scrape_task_submissions_all_time():
    services.scrape_task_submissions(to_days=300000, batch_size=15)


@scheduler.scheduled_job('interval', minutes=2)
def compute_statistics():
    stats_services.compute_user_statistics()
    stats_services.compute_task_statistics()
    stats_services.compute_ladder_statistics()


def start():
    log.info("Scheduler starting...")
    scheduler.start()
