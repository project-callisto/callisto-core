from unittest import skip

from callisto_core.delivery import forms, models, validators
from wizard_builder.forms import PageForm

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

User = get_user_model()


class ReportFlowHelper(TestCase):

    secret_key = 'super secret'
    fixtures = [
        'wizard_builder_data',
    ]

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()
        User.objects.create_user(
            username='testing_122',
            password='testing_12',
        )
        self.client.login(
            username='testing_122',
            password='testing_12',
        )

    def client_post_report_creation(self):
        response = self.client.post(
            reverse('report_new'),
            data={
                'key': self.secret_key,
                'key_confirmation': self.secret_key,
            },
            follow=True,
        )
        self.report = response.context['report']
        return response

    def client_get_report_delete(self):
        return self.client.get(
            reverse(
                'report_delete',
                kwargs={
                    'uuid': self.report.uuid,
                },
            ),
        )

    def client_get_report_view_pdf(self):
        return self.client.get(
            reverse(
                'report_view_pdf',
                kwargs={
                    'uuid': self.report.uuid,
                },
            ),
        )

    def client_post_question_answer(self, url, answer):
        return self.client.post(
            url,
            data=answer,
            follow=True,
        )

    def client_post_report_access(self, url):
        return self.client.post(
            url,
            data={
                'key': self.secret_key,
            },
            follow=True,
        )

    def client_clear_secret_key(self):
        session = self.client.session
        session['secret_key'] = None
        session.save()
        self.assertEqual(
            self.client.session.get('secret_key'),
            None,
        )


class NewReportFlowTest(ReportFlowHelper):

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
        response = self.client_post_report_creation()
        self.assertEqual(
            self.client.session.get('secret_key'),
            self.secret_key,
        )

    def test_access_form_rendered_when_no_key_in_session(self):
        response = self.client_post_report_creation()
        uuid = response.context['report'].uuid
        page_1_path = reverse('report_update', kwargs={'step': 0, 'uuid': uuid})
        self.client_clear_secret_key()

        response = self.client.get(page_1_path)
        form = response.context['form']

        self.assertIsInstance(form, forms.ReportAccessForm)

    def test_can_reenter_secret_key(self):
        response = self.client_post_report_creation()
        uuid = response.context['report'].uuid
        page_1_path = reverse('report_update', kwargs={'step': 0, 'uuid': uuid})
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
        uuid = response.context['report'].uuid
        self.client_clear_secret_key()

        self.secret_key = 'wrong key'
        response = self.client_post_report_access(
            response.redirect_chain[0][0])
        form = response.context['form']

        self.assertFalse(getattr(form, 'decrypted_report', False))
        self.assertIsInstance(form, forms.ReportAccessForm)


class ReportMetaFlowTest(ReportFlowHelper):

    def test_report_action_no_key(self):
        self.client_post_report_creation()
        self.assertTrue(self.report.pk)
        self.client_clear_secret_key()
        self.client_get_report_delete()
        self.assertTrue(self.report.pk)

    def test_report_action_invalid_key(self):
        self.client_post_report_creation()
        self.assertTrue(self.report.pk)
        self.client_clear_secret_key()
        self.secret_key = 'wrong key'
        self.client_get_report_delete()
        self.assertTrue(self.report.pk)

    def test_report_delete(self):
        self.client_post_report_creation()
        self.assertTrue(self.report.pk)
        self.client_get_report_delete()
        self.assertFalse(self.report.pk)

    def test_export_returns_pdf(self):
        self.client_post_report_creation()
        response = self.client_get_report_view_pdf()
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.get('Content-Disposition'),
            'inline; filename="report.pdf"',
        )

    def test_match_report_entry(self):
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.assertTrue(
            models.MatchReport.objects.filter(report=self.report).count(),
        )

    def test_match_report_withdrawl(self):
        self.client_post_report_creation()
        self.client_post_matching_enter()
        self.client_get_matching_withdraw()
        self.assertFalse(
            models.MatchReport.objects.filter(report=self.report).count(),
        )

    @skip('match report pdfs temporarily disabled')
    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.SiteAwareNotificationApi')
    def test_match_sends_report_immediately(self):
        response = self.client_post_match_report_submission()
        self.assertEqual(len(mail.outbox), 3)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test match notification')
        self.assertEqual(message.to, ['test1@example.com'])
        self.assertIn('Matching" <notification@', message.from_email)
        self.assertIn('test match notification body', message.body)
        message = mail.outbox[1]
        self.assertEqual(message.subject, 'test match notification')
        self.assertEqual(message.to, ['test2@example.com'])
        self.assertIn('Matching" <notification@', message.from_email)
        self.assertIn('test match notification body', message.body)
        message = mail.outbox[2]
        self.assertEqual(message.subject, 'test match delivery')
        self.assertEqual(message.to, ['titleix@example.com'])
        self.assertIn('"Reports" <reports@', message.from_email)
        self.assertIn('test match delivery body', message.body)
        self.assertRegexpMatches(message.attachments[0][0], 'report_.*\\.pdf\\.gpg')

    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.SiteAwareNotificationApi')
    @override_settings(CALLISTO_IDENTIFIER_DOMAINS=validators.facebook_or_twitter)
    def test_non_fb_match(self):
        self.client.post((self.submission_url % self.report.pk),
                         data={'name': 'test submitter 1',
                               'email': 'test1@example.com',
                               'phone_number': '555-555-1212',
                               'email_confirmation': "False",
                               'key': self.report_key,
                               'form-0-perp': 'twitter.com/trigger_a_match',
                               'form-TOTAL_FORMS': '1',
                               'form-INITIAL_FORMS': '1',
                               'form-MAX_NUM_FORMS': '', })
        response = self.client.post((self.submission_url % report2.pk),
                                    data={'name': 'test submitter 2',
                                          'email': 'test2@example.com',
                                          'phone_number': '555-555-1213',
                                          'email_confirmation': "False",
                                          'key': report2_key,
                                          'form-0-perp': 'twitter.com/Trigger_A_Match',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertNotIn('submit_error', response.context)
        self.assertEqual(len(mail.outbox), 3)
        message = mail.outbox[2]
        self.assertEqual(message.subject, 'test match delivery')
        self.assertEqual(message.to, ['titleix@example.com'])
        self.assertIn('"Reports" <reports@', message.from_email)
        self.assertIn('test match delivery body', message.body)
        self.assertRegexpMatches(message.attachments[0][0], 'report_.*\\.pdf\\.gpg')

    @skip('match report pdfs temporarily disabled')
    @override_settings(MATCH_IMMEDIATELY=False)
    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.SiteAwareNotificationApi')
    def test_match_sends_report_delayed(self):
        self.client.post((self.submission_url % self.report.pk),
                         data={'name': 'test submitter 1',
                               'email': 'test1@example.com',
                               'phone_number': '555-555-1212',
                               'email_confirmation': "False",
                               'key': self.report_key,
                               'form-0-perp': 'facebook.com/triggered_match',
                               'form-TOTAL_FORMS': '1',
                               'form-INITIAL_FORMS': '1',
                               'form-MAX_NUM_FORMS': '', })
        response = self.client.post((self.submission_url % report2.pk),
                                    data={'name': 'test submitter 2',
                                          'email': 'test2@example.com',
                                          'phone_number': '555-555-1213',
                                          'email_confirmation': "False",
                                          'key': report2_key,
                                          'form-0-perp': 'facebook.com/triggered_match',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertNotIn('submit_error', response.context)
        self.assertEqual(len(mail.outbox), 0)
        call_command('find_matches')
        self.assertEqual(len(mail.outbox), 3)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test match notification')
        self.assertEqual(message.to, ['test1@example.com'])
        self.assertIn('Matching" <notification@', message.from_email)
        self.assertIn('test match notification body', message.body)
        message = mail.outbox[1]
        self.assertEqual(message.subject, 'test match notification')
        self.assertEqual(message.to, ['test2@example.com'])
        self.assertIn('Matching" <notification@', message.from_email)
        self.assertIn('test match notification body', message.body)
        message = mail.outbox[2]
        self.assertEqual(message.subject, 'test match delivery')
        self.assertEqual(message.to, ['titleix@example.com'])
        self.assertIn('"Reports" <reports@', message.from_email)
        self.assertIn('test match delivery body', message.body)
        self.assertRegexpMatches(message.attachments[0][0], 'report_.*\\.pdf\\.gpg')

    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.CustomNotificationApi')
    def test_match_sends_custom_report(self):
        self.client.post(('/test_reports/match_custom/%s/' % self.report.pk),
                         data={'name': 'test submitter 1',
                               'email': 'test1@example.com',
                               'phone_number': '555-555-1212',
                               'email_confirmation': "False",
                               'key': self.report_key,
                               'form-0-perp': 'facebook.com/triggered_match',
                               'form-TOTAL_FORMS': '1',
                               'form-INITIAL_FORMS': '1',
                               'form-MAX_NUM_FORMS': '', })
        response = self.client.post(('/test_reports/match_custom/%s/' % report2.pk),
                                    data={'name': 'test submitter 2',
                                          'email': 'test2@example.com',
                                          'phone_number': '555-555-1213',
                                          'email_confirmation': "False",
                                          'key': report2_key,
                                          'form-0-perp': 'facebook.com/triggered_match',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertNotIn('submit_error', response.context)
        self.assertEqual(len(mail.outbox), 3)
        message = mail.outbox[2]
        self.assertEqual(message.subject, 'test match delivery')
        self.assertEqual(message.to, ['titleix@example.com'])
        self.assertIn('"Custom" <custom@', message.from_email)
        self.assertIn('test match delivery body', message.body)
        self.assertRegexpMatches(message.attachments[0][0], 'custom_.*\\.pdf\\.gpg')
