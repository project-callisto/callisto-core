from __future__ import absolute_import

import requests
from celery import shared_task

from django.conf import settings


@shared_task(name="add", bind=True)
def add(self, x, y):
    '''Demo Task for testing'''
    return x + y


@shared_task(name='send_email', bind=True)
def send_email(email_data, email_attachments=None):
    mailgun_post_route = f'https://api.mailgun.net/v3/{settings.APP_URL}/messages'
    request_params = {
        'auth': ('api', settings.MAILGUN_API_KEY),
        'data': {
            'from': f'"Callisto" <noreply@{settings.APP_URL}>',
            **email_data,
        },
        **email_attachments,
    }
    response = requests.post(self.mailgun_post_route, request_params)
    return response
