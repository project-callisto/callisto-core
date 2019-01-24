from unittest import TestCase
from unittest.mock import patch

from callisto_core.notification.api import CallistoCoreNotificationApi


class NotificationApiTestCase(TestCase):
    @patch.object(CallistoCoreNotificationApi, 'send')
    def test_send_from_template_with_path(self, send):
        template = 'template/path/email.html'
        api = CallistoCoreNotificationApi()
        api.send_from_template(template, FOO=True)
        assert send.call_count == 1
        assert api.context.get('FOO')
        assert api.context.get('email_template_name') == template

    @patch.object(CallistoCoreNotificationApi, 'send')
    def test_send_from_template_with_name(self, send):
        template = 'important_email'
        api = CallistoCoreNotificationApi()
        api.send_from_template(template, FOO=True)
        assert send.call_count == 1
        assert api.context.get('FOO')
        assert api.context.get('email_name') == template
