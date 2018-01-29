from django.test import TestCase

from callisto_core.celeryconfig.tasks import add


class TestCelery(TestCase):

    def test_add_task(self):
        add.delay(1, 2)

    def test_task_result(self):
        result = add.delay(1, 2)
        self.assertEqual(result.get(timeout=3), 3)
