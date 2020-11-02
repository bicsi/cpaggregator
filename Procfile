web: gunicorn --chdir src cpaggregator.wsgi
schedule: src/manage.py start_scheduler
worker: cd src && celery -A cpaggregator.celery worker -l INFO -E -B --concurrency 2
