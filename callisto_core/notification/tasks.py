import logging

import requests

from callisto_core.celeryconfig.celery import celery_app
from callisto_core.celeryconfig.tasks import CallistoCoreBaseTask

logger = logging.getLogger(__name__)


class _SendEmail(CallistoCoreBaseTask):
    def _setUp(self, mailgun_post_route, request_params):
        self.mailgun_post_route = mailgun_post_route
        self.request_params = request_params

    def _send_email(self):
        try:
            response = requests.post(self.mailgun_post_route, **self.request_params)
            if not response.status_code == 200:
                logger.error(
                    f"status_code!=200, content: {response.content}, params: {self.request_params}"
                )
        except Exception as exc:
            raise self.retry(exc=exc)
        return response


@celery_app.task(base=_SendEmail, bind=True, max_retries=5, soft_time_limit=5)
def SendEmail(self, mailgun_post_route, request_params):
    """Sends emails via the mailgun API"""
    self._setUp(mailgun_post_route, request_params)

    response = self._send_email()
    return response
