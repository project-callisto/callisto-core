from unittest.mock import call, patch

from callisto_core.tests.utils.api import CustomNotificationApi
from callisto_core.tests.test_base import ReportFlowHelper as ReportFlowTestCase

class ConfirmationViewTest(
    ReportFlowTestCase,
):

    DEFAULT_CALLS = [
        call(notification_name='submit_confirmation'),
        call(notification_name='report_delivery'),
        call(notification_name='submit_confirmation_callisto_team'),
    ]

    DEMO_MODE_CALLS = [
        call(notification_name='submit_confirmation'),
        call(notification_name='report_delivery'),
    ]

    def test_default_calls(self):
        with patch.object(CustomNotificationApi, '_logging') as api_logging:
            self.client_post_report_creation()
            self.client_post_reporting_end_step()

        api_logging.assert_has_calls(self.DEFAULT_CALLS, any_order=True)
