from unittest.mock import ANY, call, patch

from callisto_core.tests.test_base import (
    ReportFlowHelper as ReportFlowTestCase,
)
from callisto_core.tests.utils.api import CustomNotificationApi


class NotificationViewTest(
    ReportFlowTestCase,
):

    def test_submit_confirmation_user_email(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()
            api_logging.assert_has_calls([
                call(notification_name='submit_confirmation'),
            ], any_order=True)

    def test_submit_confirmation_slack_notification(self):
        with patch.object(CustomNotificationApi, 'slack_notification') as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()
            api_logging.assert_has_calls([
                call(msg=ANY, type='submit_confirmation'),
            ], any_order=True)
