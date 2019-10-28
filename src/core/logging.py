import logging
import sys

import loguru


class PropagateHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)


loguru.logger.add(PropagateHandler(), format="{message}")
log = loguru.logger

