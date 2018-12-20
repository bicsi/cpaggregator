from __future__ import absolute_import, unicode_literals

from .base import *
import os
from cpaggregator.celery import app as celery_app

__all__ = ['celery_app']

if os.environ.get('PRODUCTION'):
    print('IN PRODUCTION')
    from .production import *
else:
    print('LOCAL')
    from .local import *

# Other Celery settings
CELERY_BEAT_SCHEDULE = {
    # Data services cronjobs.
    'update-all-users': {
        'task': 'data.services.update_all_users',
        'schedule': 5 * 60,
    },
    'update-all-tasks-info': {
        'task': 'data.services.update_all_tasks_info',
        'schedule': 30 * 60,
    },
    'update-all-handles': {
        'task': 'data.services.update_all_handles',
        'schedule': 30 * 60,
    },
    # Scraper services cronjobs.
    'scrape-submissions-last-day': {
        'schedule': 5 * 60,
        'task': 'scraper.services.scrape_submissions_for_tasks',
        'args': ('ia:*', 'csa:*', 'cf:*'),
        'kwargs': {'to_days': 1},
    },
    'scrape-submissions-all-time': {
        'schedule': 10 * 60 * 60,
        'task': 'scraper.services.scrape_submissions_for_tasks',
        'args': ('ia:*', 'csa:*', 'cf:*'),
    },
    'scrape-tasks-info': {
        'schedule': 10,
        'task': 'scraper.services.scrape_tasks_info',
    },
    'scrape-handles-info': {
        'schedule': 10,
        'task': 'scraper.services.scrape_handles_info',
    },
    # Stats services cronjobs.
    'compute-user-statistics': {
        'schedule': 30,
        'task': 'stats.services.compute_user_statistics',
    },
    'compute-task-statistics': {
        'schedule': 5 * 60,
        'task': 'stats.services.compute_task_statistics',
    },
}
