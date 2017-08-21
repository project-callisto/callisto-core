from mock import patch

from django.test import TestCase, override_settings

from ...utils.api import MatchingApi


class ApiTest(TestCase):

    def setUp(self):
        super(ApiTest, self).setUp()
        self.mock_argument_1 = 'mock argument 1'
        self.mock_argument_2 = 'mock argument 2'

    @patch('callisto_core.matching.api.CallistoCoreMatchingApi.find_matches')
    def test_default_matching_api_call(self, mock_process):
        MatchingApi.find_matches()
        mock_process.assert_called_once_with()

    @override_settings(
        CALLISTO_MATCHING_API='callisto_core.tests.callistocore.forms.CustomMatchingApi')
    @patch('callisto_core.tests.callistocore.forms.CustomMatchingApi.run_matching')
    def test_overridden_matching_api_call(self, mock_process):
        MatchingApi.run_matching(self.mock_argument_1)
        mock_process.assert_called_once_with(self.mock_argument_1)
