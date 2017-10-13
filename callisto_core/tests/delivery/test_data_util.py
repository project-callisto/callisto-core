from pprint import pprint

from callisto_core.delivery.utils import RecordDataUtil

from django.test import TestCase

from . import record_data

from callisto_core.delivery.models import Report


class RecordIntegrationTest(TestCase):
    secret_key = 'seekritaf'

    def test_record_functionality(self):
        report = Report.objects.create()
        report.encrypt_report(record_data.EXAMPLE_SINGLE_LINE, self.secret_key)
        report.refresh_from_db()
        report_data = report.decrypted_report(self.secret_key)
        self.assertEqual(report_data, record_data.EXPECTED_SINGLE_LINE)


class DataTransformationTest(TestCase):

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
