from django.test import TestCase

from callisto_core.notification import tasks


class TestAsyncEmail(TestCase):
    def setUp(self):
        self.email_data = {
            'to': 'test@example.com',
            'subject': 'test',
            'html': '<h1>test</h1>',
            'o:testmode': 'yes',
        }

        self.email_attachments = {'files': []}

        super().setUp()

    def test_mailgun_route(self):
        SendEmail = tasks._SendEmail()
        task = SendEmail._setUp(
            domain='localhost',
            email_data=self.email_data,
            email_attachments=self.email_attachments,
        )
        self.assertIn('localhost', SendEmail.mailgun_post_route)

    def test_email_params(self):
        SendEmail = tasks._SendEmail()
        task = SendEmail._setUp(
            domain='localhost',
            email_data=self.email_data,
            email_attachments=self.email_attachments,
        )

    def test_send_email_task_submit(self):
        task = tasks.SendEmail.delay(
            domain='localhost',
            email_data=self.email_data,
            email_attachments=self.email_attachments,
        )
        self.assertIsNotNone(task)
