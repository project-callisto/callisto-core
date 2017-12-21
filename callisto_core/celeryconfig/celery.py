from __future__ import absolute_import, unicode_literals

import logging
import os

from celery import Celery

from django.conf import settings

logger = logging.getLogger(__name__)
app = Celery('celeryconfig')

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callisto_core.utils.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', '')

# Allow advanced django configurations:
if os.environ.get('DJANGO_CONFIGURATION') is not '':
    import configurations
    configurations.setup()

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
