import logging
import sys

import loguru


handler = logging.handlers.SysLogHandler(address=('localhost', 514))
loguru.logger.add(handler)
log = loguru.logger

