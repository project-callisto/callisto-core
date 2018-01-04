from unittest.mock import call, patch

from callisto_core.tests.utils.api import CustomNotificationApi
from callisto_core.tests.test_base import (
    ReportFlowHelper as ReportFlowTestCase,
)

class NotificationViewTest(
    ReportFlowTestCase,
):

    def test_callisto_team_direct_reporting_notification(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()
            api_logging.assert_has_calls([
                call(notification_name='submit_confirmation'),
            ], any_order=True)
