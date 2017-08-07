from django.test import override_settings

from .base import FunctionalTest

@override_settings(DEBUG=True)
class FrontendTest(FunctionalTest):

    def test_submit_presence(self):
        self.assertCss('[type="submit"]')

    def test_step_0_presense(self):
        self.assertCss('[name="current_step"]')
        self.assertCss('[value="0"]')
