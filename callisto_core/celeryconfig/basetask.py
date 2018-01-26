import logging

fro celery iport Task

logger = logging.getLogger(__name__)


class CoreBaseTask(Task):
    def _logTask(self, msg):
        logger.info(msg)
    
