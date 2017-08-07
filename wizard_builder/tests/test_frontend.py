from django.test import override_settings

from .base import FunctionalTest

@override_settings(DEBUG=True)
class FrontendTest(FunctionalTest):

    def test_submit_presence(self):
        pass
