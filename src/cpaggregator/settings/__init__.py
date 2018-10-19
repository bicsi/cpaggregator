from .base import *

if os.environ.get('PRODUCTION'):
    from .production import *
else:
    from .local import *
