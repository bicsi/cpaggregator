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
