import subprocess

from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()


@scheduler.scheduled_job('interval', minutes=5)
def scrape_infoarena_submissions():
    print('Scraping infoarena submissions...')
    subprocess.call('python ./src/manage.py scrape_submissions --tasks ia:* --from_days=0 --to_days=1',
                    shell=True, close_fds=True)


@scheduler.scheduled_job('interval', minutes=5)
def scrape_csacademy_submissions():
    print('Scraping csacademy submissions...')
    subprocess.call('python ./src/manage.py scrape_submissions --tasks csa:* --from_days=0 --to_days=1',
                    shell=True, close_fds=True)


@scheduler.scheduled_job('interval', minutes=5)
def scrape_codeforces_submissions():
    print('Scraping codeforces submissions...')
    subprocess.call('python ./src/manage.py scrape_submissions --tasks cf:* --from_days=0 --to_days=1',
                    shell=True, close_fds=True)


@scheduler.scheduled_job('interval', minutes=30)
def scrape_infoarena_submissions_a():
    print('Scraping infoarena submissions...')
    subprocess.call('python ./src/manage.py scrape_submissions --tasks ia:* --from_days=0 --to_days=300000',
                    shell=True, close_fds=True)
    print('Scraping infoarena tasks...')
    subprocess.call('python ./src/manage.py scrape_task_info --tasks ia:*',
                    shell=True, close_fds=True)


@scheduler.scheduled_job('interval', minutes=30)
def scrape_csacademy_submissions_a():
    print('Scraping csacademy submissions...')
    subprocess.call('python ./src/manage.py scrape_submissions --tasks csa:* --from_days=0 --to_days=300000',
                    shell=True, close_fds=True)


@scheduler.scheduled_job('interval', minutes=30)
def scrape_codeforces_submissions_a():
    print('Scraping codeforces submissions...')
    subprocess.call('python ./src/manage.py scrape_submissions --tasks cf:* --from_days=0 --to_days=300000',
                    shell=True, close_fds=True)


@scheduler.scheduled_job('interval', minutes=5)
def update_users():
    print('Updating users...')
    subprocess.call('python ./src/manage.py update_user',
                    shell=True, close_fds=True)


@scheduler.scheduled_job('interval', minutes=30)
def update_tasks():
    print('Updating tasks...')
    subprocess.call('python ./src/manage.py update_task_info',
                    shell=True, close_fds=True)

print("SCHEDULER STARTING...")
scheduler.start()
