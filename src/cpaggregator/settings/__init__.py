from .base import *
import os

if os.environ.get('PRODUCTION'):
    from .production import *
else:
    from .local import *
