from unittest import skip
from unittest.mock import MagicMock

from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from wizard_builder.forms import PageForm

from .. import test_base
from ...delivery import forms, models


class LegacyStorageFormatTest(test_base.ReportFlowHelper):

    def setUp(self):
        super().setUp()
        self.report = models.Report.objects.create()
        legacy_storage = {'data': {'catte': 'good'}}
        self.report.encrypt_report(legacy_storage, self.secret_key)
        self.client_set_secret_key()
        self.client_post_answer_question()  # prompt code to initialize storage
        self.report.refresh_from_db()
        self.storage = self.report.decrypted_report(self.secret_key)

    def test_form_data_populated(self):
        self.assertTrue(self.storage.get('wizard_form_serialized', False))

    def test_legacy_data_key_used(self):
        self.assertTrue(self.storage.get('data', False))

    def test_new_wizard_builder_key_not_used(self):
        self.assertFalse(self.storage.get('wizard_form_data', False))


class NewReportFlowTest(test_base.ReportFlowHelper):

    def test_report_creation_renders_create_form(self):
        response = self.client.get(reverse('report_new'))
        form = response.context['form']
        self.assertIsInstance(form, forms.ReportCreateForm)

    def test_report_creation_redirects_to_wizard_view(self):
        response = self.client_post_report_creation()
        uuid = response.context['report'].uuid
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse('report_update', kwargs={'step': 0, 'uuid': uuid}),
        )

    def test_report_creation_renders_wizard_form(self):
        response = self.client_post_report_creation()
        form = response.context['form']
        self.assertIsInstance(form, PageForm)

    def test_report_creation_adds_key_to_session(self):
        self.assertEqual(
            self.client.session.get('secret_key'),
            None,
        )
        self.client_post_report_creation()
        self.assertEqual(
            self.client.session.get('secret_key'),
            self.secret_key,
        )

    def test_access_form_rendered_when_no_key_in_session(self):
        response = self.client_post_report_creation()
        uuid = response.context['report'].uuid
        page_1_path = reverse(
            'report_update', kwargs={
                'step': 0, 'uuid': uuid})
        self.client_clear_secret_key()

        response = self.client.get(page_1_path)
        form = response.context['form']

        self.assertIsInstance(form, forms.ReportAccessForm)

    def test_can_reenter_secret_key(self):
        response = self.client_post_report_creation()
        uuid = response.context['report'].uuid
        page_1_path = reverse(
            'report_update', kwargs={
                'step': 0, 'uuid': uuid})
        self.client_clear_secret_key()

        response = self.client_post_report_access(page_1_path)
        self.assertRedirects(response, page_1_path)

    def test_access_form_returns_correct_report(self):
        response = self.client_post_report_creation()
        uuid = response.context['report'].uuid
        self.client_clear_secret_key()

        response = self.client_post_report_access(
            response.redirect_chain[0][0])

        self.assertEqual(response.context['report'].uuid, uuid)

    def test_report_not_accessible_with_incorrect_key(self):
        response = self.client_post_report_creation()
        self.client_clear_secret_key()

        self.secret_key = 'wrong key'
        response = self.client_post_report_access(
            response.redirect_chain[0][0])
        form = response.context['form']

        self.assertFalse(getattr(form, 'decrypted_report', False))
        self.assertIsInstance(form, forms.ReportAccessForm)


class ReportMetaFlowTest(test_base.ReportFlowHelper):

    def test_report_action_no_key(self):
        self.client_post_report_creation()
        self.assertTrue(self.report.pk)
        self.client_clear_secret_key()
        self.client_post_report_delete()
        self.assertFalse(self.assert_report_exists())

    def test_report_action_invalid_key(self):
        self.client_post_report_creation()
        self.assertTrue(self.report.pk)
        self.client_clear_secret_key()
        self.secret_key = 'wrong key'
        self.client_post_report_delete()
        self.assertTrue(self.assert_report_exists())

    def test_report_delete(self):
        self.client_post_report_creation()
        self.assertTrue(self.report.pk)
        response = self.client_post_report_delete()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.assert_report_exists())

    def test_export_returns_pdf(self):
        self.client_post_report_creation()
        response = self.client_get_report_view_pdf()
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.get('Content-Disposition'),
            'inline; filename="report.pdf"',
        )

    @skip('temporariy disabled')
    def test_match_report_entry(self):
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.assertTrue(
            models.MatchReport.objects.filter(report=self.report).count(),
        )

    @skip('temporariy disabled')
    def test_match_report_withdrawl(self):
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.client_get_matching_withdraw()
        self.assertFalse(
            models.MatchReport.objects.filter(report=self.report).count(),
        )

    @skip('temporariy disabled')
    @override_settings(
        CALLISTO_NOTIFICATION_API='tests.callistocore.forms.SiteAwareNotificationApi')
    def test_match_sends_report_immediately(self):
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.match_report_email_assertions()

    @skip('temporariy disabled')
    @override_settings(MATCH_IMMEDIATELY=False)
    @override_settings(
        CALLISTO_NOTIFICATION_API='tests.callistocore.forms.SiteAwareNotificationApi')
    def test_match_sends_report_delayed(self):
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.assertEqual(len(mail.outbox), 0)
        call_command('find_matches')
        self.match_report_email_assertions()
