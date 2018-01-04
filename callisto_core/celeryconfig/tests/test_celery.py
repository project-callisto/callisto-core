from django.test import TestCase

from callisto_core.celeryconfig.tasks import add, send_email


class TestCelery(TestCase):

    def test_add_task(self):
        add.delay(1, 2)

    def test_task_result(self):
        result = add.delay(1, 2)
        self.assertEqual(result.get(timeout=3), 3)


class TestAsyncEmail(TestCase):

    def test_send_email_basic_case(self):
        send_email.delay(
            email_data={
                'to': 'test@example.com',
                'subject': 'test',
                'html': '<h1>test</h1>',
                'o:testmode': 'yes',
            },
            email_attachments=None,
        )
