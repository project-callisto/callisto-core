from django.test import TestCase

from callisto_core.notification import tasks


class TestAsyncEmail(TestCase):

    def test_send_email_basic_case(self):
        tasks.SendEmail.delay(
            domain='localhost',
            email_data={
                'to': 'test@example.com',
                'subject': 'test',
                'html': '<h1>test</h1>',
                'o:testmode': 'yes',
            },
            email_attachments=None,
        )
