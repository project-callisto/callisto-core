from django.test import TestCase
from django.test.utils import override_settings

from callisto_core.celeryconfig.tasks import add


class AddTestCase(TestCase):

    def test_mytask(self):
        result = add.delay(1, 2)
        self.assertTrue(result.successful())
