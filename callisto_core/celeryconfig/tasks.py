from __future__ import absolute_import

import logging

import requests
from celery import Task, shared_task

from django.conf import settings

logger = logging.getLogger(__name__)


class CoreBaseTask(Task):
    """Abstract base class for all callisto-core tasks"""

    abstract = True

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


@shared_task(name="add", bind=True)
def add(self, x, y):
    '''Demo Task for testing'''
    return x + y
