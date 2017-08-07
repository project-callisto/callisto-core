from django.test import override_settings

from .base import FunctionalTest

@override_settings(DEBUG=True)
class FrontendTest(FunctionalTest):

    def test_submit_presence(self):
        self.assertTrue(
            self.browser.find_elements_by_css_selector('[type="submit"]'),
        )
