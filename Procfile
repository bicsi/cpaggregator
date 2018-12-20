web: gunicorn --chdir src cpaggregator.wsgi
clock: python clock.py
worker: "cd src && celery -A cpaggregator.celery worker -l DEBUG -E"
