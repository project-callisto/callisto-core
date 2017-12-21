from __future__ import absolute_import

from celery import shared_task


'''
Demo Task for testing
'''


@shared_task(name="add")
def add(x, y):
    return x + y
