from __future__ import absolute_import

import requests
from celery import shared_task

from django.conf import settings


@shared_task(name="add", bind=True)
def add(self, x, y):
    '''Demo Task for testing'''
    return x + y
