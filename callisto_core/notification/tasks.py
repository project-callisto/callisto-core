import requests

from django.conf import settings

from callisto_core.celeryconfig.celery import celery_app
from callisto_core.celeryconfig.tasks import CallistoCoreBaseTask


class _SendEmail(CallistoCoreBaseTask):

    def _setUp(self, domain, email_data, email_attachments):
        self._set_mailgun_route(domain)
        self._set_params(domain, email_data, email_attachments)

    def _set_mailgun_route(self, domain):
        self.mailgun_post_route = f'https://api.mailgun.net/v3/{domain}/messages'

    def _set_params(self, domain, email_data, email_attachments):
        self.request_params = {
            'auth': ('api', settings.MAILGUN_API_KEY),
            'data': {
                'from': f'"Callisto" <noreply@{domain}>',
                **email_data,
            },
            **email_attachments,
        }

    def _send_email(self):
        try:
            response = requests.post(
                self.mailgun_post_route,
                self.request_params)
        except Exception as exc:
            raise self.retry(exc=exc)
        return response


@celery_app.task(base=_SendEmail,
                 bind=True,
                 max_retries=5,
                 soft_time_limit=5)
def SendEmail(self, domain, email_data, email_attachments):
    """Sends emails via the mailgun API"""
    self._setUp(domain, email_data, email_attachments)

    response = self._send_email()
    return response
