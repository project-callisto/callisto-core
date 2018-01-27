from callisto_core.celeryconfig import celery_app
from callisto_core.celeryconfig.tasks import CoreBaseTask

from django.conf import settings


@celery_app.task(base=CoreBaseTask, bind=True)
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
