web: gunicorn --chdir src cpaggregator.wsgi
clock: python clock.py
worker: celery -A cpaggregator.celery worker -l INFO -E --workdir src -B
