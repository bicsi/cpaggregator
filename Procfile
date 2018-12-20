web: gunicorn --chdir src cpaggregator.wsgi
clock: python clock.py
worker: celery --chdir src -A cpaggregator.celery worker -l DEBUG -E
