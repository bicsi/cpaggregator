web: gunicorn --chdir src cpaggregator.wsgi
clock: python clock.py
worker: celery -A cpaggregator.celery worker -l DEBUG -E --workdir src -B
