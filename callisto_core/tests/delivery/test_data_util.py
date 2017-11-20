from pprint import pprint

from django.test import TestCase

from callisto_core.delivery.models import Report
from callisto_core.delivery.utils import RecordDataUtil
from wizard_builder.view_helpers import SerializedDataHelper

from . import record_data


class RecordIntegrationTest(TestCase):
    passphrase = 'seekritaf'

    def test_record_functionality(self):
        report = Report.objects.create()
        report.encrypt_report(record_data.EXAMPLE_SINGLE_LINE, self.passphrase)
        report.refresh_from_db()
        report_data = report.decrypted_report(self.passphrase)
        self.assertEqual(report_data, record_data.EXPECTED_SINGLE_LINE)


class DataTransformationTest(TestCase):

    def assertListItemsUnique(self, items):
        items_set = set(items)
        self.assertEqual(
            len(set(items)),
            len(items),
        )

    def test_single_line_text_form(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_SINGLE_LINE)
        self.assertEqual(
            data['wizard_form_serialized'][0][0],
            record_data.EXPECTED_SINGLE_LINE['wizard_form_serialized'][0][0],
        )

    def test_single_question_answers(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_SINGLE_RADIO)
        self.assertEqual(
            data['data'],
            record_data.EXPECTED_SINGLE_RADIO['data'])

    def test_single_question_form(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_SINGLE_RADIO)
        self.assertEqual(
            data['wizard_form_serialized'][0][0],
            record_data.EXPECTED_SINGLE_RADIO['wizard_form_serialized'][0][0],
        )

    def test_page_count(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_FORMSET)
        self.assertEqual(len(data['wizard_form_serialized']), 2)
        self.assertEqual(
            len(data['wizard_form_serialized']),
            len(record_data.EXPECTED_FORMSET['wizard_form_serialized']),
        )

    def test_single_question_both(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_SINGLE_RADIO)
        self.assertEqual(data, record_data.EXPECTED_SINGLE_RADIO)

    def test_new_data_not_transformed(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXPECTED_SINGLE_RADIO)
        self.assertEqual(data, record_data.EXPECTED_SINGLE_RADIO)

    def test_formset(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_FORMSET)
        for index, transformed_page in enumerate(
                data['wizard_form_serialized']):
            expected_page = record_data.EXPECTED_FORMSET['wizard_form_serialized'][index]

    def test_full_data_first_page_not_empty(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_FULL_DATASET)
        self.assertNotEqual(data['wizard_form_serialized'][0], [])

    def test_full_data_last_page_not_empty(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_FULL_DATASET)
        self.assertNotEqual(data['wizard_form_serialized'][-1], [])

    def test_full_dataset_all_answered(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_FULL_DATASET)
        formatted_data = SerializedDataHelper.get_zipped_data(
            data=data['data'],
            forms=data['wizard_form_serialized'],
        )
        for item in formatted_data:
            answer = list(item.values())[0][0]
            self.assertNotEqual(answer, SerializedDataHelper.not_answered_text)

    def test_full_dataset_formset_answers_not_lost(self):
        data = RecordDataUtil.transform_if_old_format(
            record_data.EXAMPLE_FULL_DATASET)
        formatted_data_string = str(SerializedDataHelper.get_zipped_data(
            data=data['data'],
            forms=data['wizard_form_serialized'],
        ))
        self.assertIn('1 example data', formatted_data_string)
        self.assertIn('2 example data', formatted_data_string)
        self.assertIn('USF Undergraduate student', formatted_data_string)
        self.assertIn('Friend or visitor on campus', formatted_data_string)
