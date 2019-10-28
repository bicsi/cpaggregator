import logging
import os
import sys

import loguru

if os.environ.get('PRODUCTION'):
    log = logging.getLogger(__name__)
else:
    log = loguru.logger

