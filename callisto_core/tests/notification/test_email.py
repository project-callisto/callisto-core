from unittest import skip

from django.conf import settings
from django.test import TestCase

from callisto_core.notification import tasks


class TestAsyncEmail(TestCase):
    TEST_DOMAIN = "localhost"

    def setUp(self):
        self.mailgun_post_route = (
            f"https://api.mailgun.net/v3/{self.TEST_DOMAIN}/messages"
        )
        self.request_params = {
            "auth": ("api", settings.MAILGUN_API_KEY),
            "data": {
                "from": "test@example.com",
                "to": "test@example.com",
                "subject": "test",
                "html": "<h1>test</h1>",
                "o:testmode": "yes",
            },
            "files": [],
        }
        super().setUp()

    @skip("TODO: re-enable when celery config is finished")
    def test_mailgun_route(self):
        SendEmail = tasks._SendEmail()
        task = SendEmail._setUp(self.mailgun_post_route, self.request_params)
        self.assertIn(self.TEST_DOMAIN, SendEmail.mailgun_post_route)

    @skip("TODO: re-enable when celery config is finished")
    def test_email_params(self):
        SendEmail = tasks._SendEmail()
        task = SendEmail._setUp(self.mailgun_post_route, self.request_params)

    @skip("TODO: re-enable when celery config is finished")
    def test_send_email_task_submit(self):
        SendEmail = tasks._SendEmail()
        task = SendEmail._setUp(self.mailgun_post_route, self.request_params)
        self.assertIsNotNone(task)
