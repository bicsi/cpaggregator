import subprocess

from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()


@scheduler.scheduled_job('interval', minutes=5)
def scrape_infoarena_submissions():
    print('Scraping infoarena submissions...')
    subprocess.call('python ./src/manage.py scrape_submissions --tasks ia:* --from_days=0 --to_days=7',
                    shell=True, close_fds=True)


@scheduler.scheduled_job('interval', minutes=5)
def update_users():
    print('Updating users...')
    subprocess.call('python ./src/manage.py update_user',
                    shell=True, close_fds=True)

scheduler.start()
