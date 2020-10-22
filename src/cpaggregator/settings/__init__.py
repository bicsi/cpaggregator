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
        'schedule': 2 * 60,
    },
    'update-all-tasks-info': {
        'task': 'data.services.update_all_tasks_info',
        'schedule': 30 * 60,
    },
    # 'update-all-handles': {
    #     'task': 'data.services.update_all_handles',
    #     'schedule': 30 * 60,
    # },

    # Scraper services cronjobs.
    'scrape-recent-submissions': {
        'schedule': 30,
        'task': 'scraper.services.scrape_recent_submissions',
        'args': ('ia', 'cf'),
        'kwargs': {'to_days': 1},
    },
    'scrape-submissions-tasks-last-day': {
        'schedule': 5 * 60,
        'task': 'scraper.services.scrape_submissions_for_tasks',
        'args': ('ac/*', 'ojuz/*'),
        'kwargs': {'to_days': 1},
    },
    'scrape-submissions-tasks-all-time': {
        'schedule': 10 * 60 * 60,
        'task': 'scraper.services.scrape_submissions_for_tasks',
        'args': ('ac/*', 'ojuz/*'),
    },
    'scrape-submissions-users-last-day': {
        'schedule': 5 * 60,
        'task': 'scraper.services.scrape_submissions_for_users',
        'args': ('cf/*', 'ia/*', 'timus/*', 'csa/*'),
        'kwargs': {'to_days': 1},
    },
    'scrape-submissions-users-all-time': {
        'schedule': 10 * 60 * 60,
        'task': 'scraper.services.scrape_submissions_for_users',
        'args': ('cf/*', 'ia/*', 'timus/*', 'csa/*'),
    },
    # 'scrape-tasks-info': {
    #    'schedule': 60 * 60,
    #    'task': 'scraper.services.scrape_tasks_info',
    # },
    'scrape-handles-info': {
        'schedule': 60 * 60,
        'task': 'scraper.services.scrape_handles_info',
    },
    # Stats services cronjobs.
    'compute-user-statistics': {
        'schedule': 10 * 60,
        'task': 'stats.services.compute_user_statistics',
    },
    'compute-task-statistics': {
        'schedule': 10 * 60,
        'task': 'stats.services.compute_task_statistics',
    },
    'compute-ladder-statistics': {
        'schedule': 10 * 60,
        'task': 'stats.services.compute_ladder_statistics',
    },
}
