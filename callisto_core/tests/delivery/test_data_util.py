from callisto_core.delivery.utils import RecordDataUtil

from django.test import TestCase

from . import record_data


class DataTransformationTest(TestCase):

    def test_single_question_answers_equal(self):
        data = RecordDataUtil.transform_if_old_format(record_data.EXAMPLE_1A)
        self.assertEqual(data['data'], record_data.EXAMPLE_2A['data'])

    def test_single_question_form_equal(self):
        data = RecordDataUtil.transform_if_old_format(record_data.EXAMPLE_1A)
        self.assertEqual(
            data['wizard_form_serialized'],
            record_data.EXAMPLE_2A['wizard_form_serialized'],
        )

    def test_single_question_both_equal(self):
        data = RecordDataUtil.transform_if_old_format(record_data.EXAMPLE_1A)
        self.assertEqual(data, record_data.EXAMPLE_2A)

    def test_new_data_not_transformed(self):
        data = RecordDataUtil.transform_if_old_format(record_data.EXAMPLE_2A)
        self.assertEqual(data, record_data.EXAMPLE_2A)
