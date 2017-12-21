from celeryconfig.tasks import add

from django.test import TestCase
from django.test.utils import override_settings


class AddTestCase(TestCase):

    def test_mytask(self):
        result = add.delay(1, 2)
        self.assertTrue(result.successful())
