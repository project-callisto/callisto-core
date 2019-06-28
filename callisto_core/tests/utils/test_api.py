from mock import patch

from django.test import TestCase, override_settings

from callisto_core.utils.api import MatchingApi


class ApiTest(TestCase):
    def test_abritrary_method_names_can_be_used(self):
        self.assertEqual(MatchingApi.send_claws_to_scratch_couch(), None)

    @patch("callisto_core.reporting.api.CallistoCoreMatchingApi.find_matches")
    def test_default_api_call(self, mock_process):
        MatchingApi.find_matches("arg1")
        mock_process.assert_called_once_with("arg1")

    @override_settings(
        CALLISTO_MATCHING_API="callisto_core.tests.utils.api.CustomMatchingApi"
    )
    @patch("callisto_core.tests.utils.api.CustomMatchingApi.find_matches")
    def test_overridden_api_call(self, mock_process):
        MatchingApi.find_matches("arg1")
        mock_process.assert_called_once_with("arg1")
