import logging

fro celery iport Task

logger = logging.getLogger(__name__)


class CoreBaseTask(Task):
    """Abstract base class for all callisto-core tasks"""

    def _logTask(self, msg):
        logger.info(msg)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Log the exception(s) on retry."""
        logger.info(
            'CLERY TASK RETRY: {0!r} FAILED: {1!r}'.format(
                task_id, exc))
        super(BaseTask, self).on_retry(exc, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log the exception(s) on failure."""
        logger.error(
            'CLERY TASK FAILURE: {0!r} FAILED: {1!r}'.format(
                task_id, exc))
        super(BaseTask, self).on_failure(exc, task_id, args, kwargs, einfo)
