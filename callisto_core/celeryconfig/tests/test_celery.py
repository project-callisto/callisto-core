from pytest import raises

from celery.exceptions import Retry
from callisto_core.celeryconfig.tasks import add

# for python 2: use mock.patch from `pip install mock`.
from unittest.mock import patch
from unittest import TestCase
from django.test import TestCase, override_settings

class TestCelery(TestCase):
    
    def test_add_task(self):
        add.delay(1, 2)

    def test_task_result(self):
        result = add.delay(1, 2)
        self.assertEqual(result.get(timeout=3), 3)
