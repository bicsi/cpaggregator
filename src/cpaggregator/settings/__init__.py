from .base import *
import os

if os.environ.get('PRODUCTION'):
    print('IN PRODUCTION')
    from .production import *
else:
    print('LOCAL')
    from .local import *
