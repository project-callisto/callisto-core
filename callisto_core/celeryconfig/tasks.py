from __future__ import absolute_import

from celery import shared_task


'''
Demo Task for testing
'''


@shared_task(name="add", bind=True)
def add(self, x, y):
    return x + y
