from callisto_core.delivery.utils import RecordDataUtil

from django.test import TestCase

from . import record_data


class DataTransformationTest(TestCase):

    def test_single_question_example(self):
        data = RecordDataUtil.transform_if_old_format(record_data.EXAMPLE_1A)
        self.assertEqual(data, record_data.EXAMPLE_2A)

    def test_new_data_not_transformed(self):
        data = RecordDataUtil.transform_if_old_format(record_data.EXAMPLE_2A)
        self.assertEqual(data, record_data.EXAMPLE_2A)
