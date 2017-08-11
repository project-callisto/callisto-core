import json
from io import BytesIO

import PyPDF2
from mock import patch
from tests.callistocore.forms import CustomNotificationApi
from wizard_builder.forms import PageForm
from wizard_builder.models import (
    Choice, Page, RadioButton, SingleLineText,
)

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.core.management import call_command
from django.http import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings

from callisto_core.delivery import validators
from callisto_core.utils.api import NotificationApi
from callisto_core.delivery.forms import NewSecretKeyForm, SecretKeyForm
from callisto_core.delivery.models import MatchReport, Report, SentFullReport
from callisto_core.evaluation.models import EvalRow
from callisto_core.notification.models import EmailNotification

User = get_user_model()


def sort_json(text):
    return sorted(json.loads(text), key=lambda x: x['id'])


def get_body(response):
    return response.content.decode('utf-8')


class SiteAwareTestCase(TestCase):

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()


class RecordFormBaseTest(SiteAwareTestCase):

    def setUp(self):
        super(RecordFormBaseTest, self).setUp()
        self.page1 = Page.objects.create()
        self.page1.sites.add(self.site.id)
        self.page2 = Page.objects.create()
        self.page2.sites.add(self.site.id)
        self.question1 = SingleLineText.objects.create(text="first question", page=self.page1)
        self.question2 = SingleLineText.objects.create(text="2nd question", page=self.page2)

    def _get_wizard_response(self, wizard, form_list, **kwargs):
        # simulate what wizard does on final form 7
        wizard.processed_answers = wizard.process_answers(form_list=form_list, form_dict=dict(enumerate(form_list)))
        return get_body(wizard.done(form_list=form_list, form_dict=dict(enumerate(form_list)), **kwargs))


class RecordFormIntegratedTest(RecordFormBaseTest):

    def setUp(self):
        super(RecordFormIntegratedTest, self).setUp()
        User.objects.create_user(username='dummy', password='dummy')
        self.client.login(username='dummy', password='dummy')
        self.request = HttpRequest()
        self.request.GET = {}
        self.request.method = 'GET'
        self.request.user = User.objects.get(username='dummy')

    record_form_url = '/test_reports/new/0/'
    report_key = 'solidasarock1234rock'

    def create_key(self):
        return self.client.post(
            self.record_form_url,
            data={'0-key': self.report_key,
                  '0-key2': self.report_key,
                  'form_wizard-current_step': 0},
            follow=True
        )

    def test_new_record_page_renders_key_template(self):
        response = self.client.get(self.record_form_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_key.html')

    def test_new_record_form_advances_to_second_page(self):
        response = self.create_key()
        self.assertTemplateUsed(response, 'record_form.html')
        self.assertIsInstance(response.context['form'], PageForm)
        self.assertContains(response, 'name="1-question_%i"' % self.question1.pk)
        self.assertNotContains(response, 'name="1-question_%i"' % self.question2.pk)

    def test_auto_save(self):
        response = self.create_key()
        self.client.post(
            response.redirect_chain[0][0],
            data={
                '1-question_{}'.format(self.question1.pk): 'test answer',
                'form_wizard-current_step': 1,
                'wizard_goto_step': 2,
            },
            follow=True,
        )
        self.assertEqual(Report.objects.count(), 1)

    def test_auto_save_is_set_correctly(self):
        # record flagged as autosave on an autosaved record
        response = self.create_key()
        self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question1.pk: 'test answer',
                  'form_wizard-current_step': 1,
                  'wizard_goto_step': 2},
            follow=True)
        self.assertTrue(Report.objects.first().autosaved)

    def test_auto_save_not_set_incorrectly(self):
        # record is not flagged as autosave on an explicitly saved record
        # need to load first page of record form because that's how storage gets reset
        self.client.get(self.record_form_url, follow=True)
        self.assertTemplateUsed('record_form.html')
        response = self.create_key()
        response = self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question1.pk: 'test answer',
                  'form_wizard-current_step': 1},
            follow=True)
        self.client.post(
            response.redirect_chain[0][0],
            data={'2-question_%i' % self.question2.pk: 'another answer to a different question',
                  'form_wizard-current_step': 2},
            follow=True)
        self.assertEqual(Report.objects.count(), 2)
        self.assertFalse(Report.objects.latest('id').autosaved)


class ExistingRecordTest(RecordFormBaseTest):

    def setUp(self):
        super(ExistingRecordTest, self).setUp()

        User.objects.create_user(username='dummy', password='dummy')
        self.client.login(username='dummy', password='dummy')
        self.request = HttpRequest()
        self.request.GET = {}
        self.request.method = 'GET'
        self.request.user = User.objects.get(username='dummy')

        self.report_text = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]""" % (self.question1.pk, self.question2.pk)
        self.report = Report(owner=self.request.user)
        self.report_key = 'bananabread! is not my key'
        self.report.encrypt_report(self.report_text, self.report_key)
        self.report.save()
        row = EvalRow()
        row.anonymise_record(action=EvalRow.CREATE, report=self.report, decrypted_text=self.report_text)
        row.save()


class SubmitReportIntegrationTest(ExistingRecordTest):

    submission_url = '/test_reports/submit/%s/'

    def setUp(self):
        super(SubmitReportIntegrationTest, self).setUp()
        EmailNotification.objects.create(
            name='submit_confirmation',
            subject="test submit confirmation",
            body="test submit confirmation body",
        ).sites.add(self.site.id)
        EmailNotification.objects.create(
            name='report_delivery',
            subject="test delivery",
            body="test body",
        ).sites.add(self.site.id)

    def test_renders_default_template(self):
        response = self.client.get(self.submission_url % self.report.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submit_report_to_authority.html')

    def test_renders_custom_template(self):
        response = self.client.get('/test_reports/submit_custom/%s/' % self.report.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submit_report_to_authority_custom.html')

    def test_renders_default_confirmation_template(self):
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertTemplateUsed(response, 'submit_report_to_authority_confirmation.html')

    def test_renders_custom_confirmation_template(self):
        response = self.client.post(('/test_reports/submit_custom/%s/' % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertIn('custom context', get_body(response))
        self.assertTemplateUsed(response, 'submit_report_to_authority_confirmation_custom.html')

    def test_submit_sends_report(self):
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test delivery')
        self.assertIn('"Reports" <reports', message.from_email)
        self.assertEqual(message.to, ['titleix@example.com'])
        self.assertRegexpMatches(message.attachments[0][0], 'report_.*\\.pdf\\.gpg')

    @override_settings(COORDINATOR_EMAIL='titleix1@example.com,titleix2@example.com')
    def test_submit_sends_report_to_multiple_coordinators(self):
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(SentFullReport.objects.count(), 1)
        message1 = mail.outbox[0]
        self.assertEqual(message1.subject, 'test delivery')
        self.assertIn('"Reports" <reports', message1.from_email)
        self.assertEqual(message1.to, ['titleix1@example.com', 'titleix2@example.com'])
        self.assertRegexpMatches(message1.attachments[0][0], 'report_.*\\.pdf\\.gpg')

    def test_submit_sends_email_confirmation(self):
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': True,
                                          'key': self.report_key})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertEqual(len(mail.outbox), 2)
        message = mail.outbox[1]
        self.assertEqual(message.subject, 'test submit confirmation')
        self.assertIn('Confirmation" <confirmation@', message.from_email)
        self.assertEqual(message.to, ['test@example.com'])
        self.assertIn('test submit confirmation body', message.body)

    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.CustomNotificationApi')
    def test_submit_sends_custom_report(self):
        response = self.client.post(('/test_reports/submit_custom/%s/' % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test delivery')
        self.assertIn('"Custom" <custom', message.from_email)
        self.assertEqual(message.to, ['titleix@example.com'])
        self.assertRegexpMatches(message.attachments[0][0], 'custom_.*\\.pdf\\.gpg')

    @patch('callisto_core.notification.api.CallistoCoreNotificationApi.send_report_to_authority')
    def test_submit_exception_is_handled(self, mock_send_report_to_authority):
        mock_send_report_to_authority.side_effect = Exception('Mock Send Report Exception')
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key})
        self.assertIn('submit_error', response.context)

    @patch('callisto_core.delivery.views.logger')
    @patch('callisto_core.notification.api.CallistoCoreNotificationApi.send_user_notification')
    def test_submit_email_confirmation_is_handled(self, mock_send_user_notification, mock_logger):
        mock_send_user_notification.side_effect = Exception('Mock Send Confirmation Exception')
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "True",
                                          'key': self.report_key})
        self.assertTrue(mock_logger.exception.called)
        mock_logger.exception.assert_called_with("couldn't send confirmation to user on submission")
        self.assertTemplateNotUsed(response, 'submit_report_to_authority.html')


class SubmitMatchIntegrationTest(ExistingRecordTest):

    submission_url = '/test_reports/match/%s/'

    def setUp(self):
        super(SubmitMatchIntegrationTest, self).setUp()
        EmailNotification.objects.create(
            name='match_confirmation',
            subject="test match confirmation",
            body="test match confirmation body",
        ).sites.add(self.site.id)
        EmailNotification.objects.create(
            name='match_notification',
            subject="test match notification",
            body="test match notification body",
        ).sites.add(self.site.id)
        EmailNotification.objects.create(
            name='match_delivery',
            subject="test match delivery",
            body="test match delivery body",
        ).sites.add(self.site.id)

    def test_renders_default_template(self):
        response = self.client.get(self.submission_url % self.report.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submit_to_matching.html')

    def test_renders_custom_template(self):
        response = self.client.get('/test_reports/match_custom/%s/' % self.report.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn('custom context', get_body(response))
        self.assertTemplateUsed(response, 'submit_to_matching_custom.html')

    def test_renders_default_confirmation_template(self):
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key,
                                          'form-0-perp': 'facebook.com/test_url',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertTemplateUsed(response, 'submit_to_matching_confirmation.html')

    def test_renders_custom_confirmation_template(self):
        response = self.client.post(('/test_reports/match_custom/%s/' % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key,
                                          'form-0-perp': 'facebook.com/test_url',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertTemplateUsed(response, 'submit_to_matching_confirmation_custom.html')

    def test_submit_creates_match(self):
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key,
                                          'form-0-perp': 'facebook.com/test_url',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertEqual(self.report.id, MatchReport.objects.latest('id').report.id)

    def test_multiple_perps_creates_multiple_matches(self):
        total_matches_before = MatchReport.objects.count()
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key,
                                          'form-0-perp': 'facebook.com/test_url1',
                                          'form-1-perp': 'facebook.com/test_url2',
                                          'form-TOTAL_FORMS': '2',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        total_matches_after = MatchReport.objects.count()
        self.assertEqual(total_matches_after - total_matches_before, 2)

    def test_submit_match_sends_email_confirmation(self):
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': True,
                                          'key': self.report_key,
                                          'form-0-perp': 'facebook.com/test_url',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'test match confirmation')
        self.assertEqual(message.to, ['test@example.com'])
        self.assertIn('Confirmation" <confirmation@', message.from_email)
        self.assertIn('test match confirmation body', message.body)

    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.SiteAwareNotificationApi')
    def test_match_sends_report_immediately(self):
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
        user2 = User.objects.create_user(username='dummy2', password='dummy')
        self.client.login(username='dummy2', password='dummy')
        report2_text = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]""" % (self.question1.pk, self.question2.pk)
        report2 = Report(owner=user2)
        report2_key = 'a key a key a key a key key'
        report2.encrypt_report(report2_text, report2_key)
        report2.save()
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
        user2 = User.objects.create_user(username='dummy2', password='dummy')
        self.client.login(username='dummy2', password='dummy')
        report2_text = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]""" % (self.question1.pk, self.question2.pk)
        report2 = Report(owner=user2)
        report2_key = 'a key a key a key a key key'
        report2.encrypt_report(report2_text, report2_key)
        report2.save()
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
        user2 = User.objects.create_user(username='dummy2', password='dummy')
        self.client.login(username='dummy2', password='dummy')
        report2_text = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]""" % (self.question1.pk, self.question2.pk)
        report2 = Report(owner=user2)
        report2_key = 'a key a key a key a key key'
        report2.encrypt_report(report2_text, report2_key)
        report2.save()
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
        user2 = User.objects.create_user(username='dummy2', password='dummy')
        self.client.login(username='dummy2', password='dummy')
        report2_text = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]""" % (self.question1.pk, self.question2.pk)
        report2 = Report(owner=user2)
        report2_key = 'a key a key a key a key key'
        report2.encrypt_report(report2_text, report2_key)
        report2.save()
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

    @override_settings(CALLISTO_MATCHING_API='tests.callistocore.forms.CustomMatchingApi')
    @patch('tests.callistocore.forms.CustomMatchingApi.run_matching')
    def test_match_calls_custom_matching_api(self, mock_process):
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
        mock_process.assert_called_once()

    @patch('callisto_core.delivery.views.MatchReport.encrypt_match_report')
    def test_match_send_exception_is_handled(self, mock_encrypt_match_report):
        mock_encrypt_match_report.side_effect = Exception('Mock Submit Match Exception')
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.report_key,
                                          'form-0-perp': 'facebook.com/test_url',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertIn('submit_error', response.context)

    @patch('callisto_core.delivery.views.logger')
    @patch('callisto_core.notification.api.CallistoCoreNotificationApi.send_user_notification')
    def test_match_email_confirmation_exception_is_handled(self, mock_send_user_notification, mock_logger):
        mock_send_user_notification.side_effect = Exception('Mock Send Confirmation Exception')
        response = self.client.post((self.submission_url % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "True",
                                          'key': self.report_key,
                                          'form-0-perp': 'facebook.com/test_url',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertTrue(mock_logger.exception.called)
        mock_logger.exception.assert_called_with("couldn't send confirmation to user on match submission")
        self.assertTemplateNotUsed(response, 'submit_to_matching.html')


class WithdrawMatchIntegrationTest(ExistingRecordTest):

    withdrawal_url = '/test_reports/withdraw_match/%s/'

    def setUp(self):
        super(WithdrawMatchIntegrationTest, self).setUp()
        match_report = MatchReport()
        match_report.report = self.report
        match_report.contact_email = "test@example.com"
        match_report.identifier = "http://www.facebook.com/test_withdrawal"
        match_report.save()
        self.match_report = match_report

    def test_renders_specified_template(self):
        response = self.client.get(self.withdrawal_url % self.report.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn('custom context', get_body(response))
        self.assertTemplateUsed(response, 'after_withdraw.html')

    def test_match_report_is_withdrawn(self):
        self.assertEqual(MatchReport.objects.filter(report=self.report).count(), 1)
        response = self.client.get(self.withdrawal_url % self.report.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MatchReport.objects.filter(report=self.report).count(), 0)


class ExportRecordViewTest(ExistingRecordTest):

    export_url = "/test_reports/export/%i/"

    def test_export_requires_key(self):
        response = self.client.get(self.export_url % self.report.id)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'export_report.html')
        self.assertIsInstance(response.context['form'], SecretKeyForm)

    def test_export_passes_custom_context(self):
        response = self.client.get("/test_reports/export_custom/%i/" % self.report.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('custom context', get_body(response))

    def test_export_requires_correct_key(self):
        response = self.client.post(
            (self.export_url % self.report.id),
            data={'key': "abracadabra"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'export_report.html')
        form = response.context['form']
        self.assertIsInstance(form, SecretKeyForm)
        self.assertContains(response, "The passphrase didn&#39;t match.")

    def test_export_returns_pdf(self):
        response = self.client.post(
            (self.export_url % self.report.id),
            data={'key': self.report_key},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEquals(
            response.get('Content-Disposition'),
            'attachment; filename="report.pdf"'
        )

    def test_export_pdf_has_report(self):
        response = self.client.post(
            (self.export_url % self.report.id),
            data={'key': self.report_key},
        )
        self.assertEqual(response.status_code, 200)
        exported_report = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfFileReader(exported_report)
        self.assertNotIn("Tatiana Nine", pdf_reader.getPage(0).extractText())
        self.assertIn("Reported by: dummy", pdf_reader.getPage(0).extractText())
        self.assertIn("test answer", pdf_reader.getPage(1).extractText())
        self.assertIn("another answer to a different question", pdf_reader.getPage(1).extractText())

    @override_settings(CALLISTO_NOTIFICATION_API='tests.callistocore.forms.CustomNotificationApi')
    def test_export_pdf_uses_custom_report(self):
        response = self.client.post(
            ("/test_reports/export_custom/%i/" % self.report.id),
            data={'key': self.report_key},
        )
        self.assertEqual(response.status_code, 200)
        exported_report = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfFileReader(exported_report)
        self.assertEqual(NotificationApi.report_title, CustomNotificationApi.report_title)
        self.assertIn(CustomNotificationApi.report_title, pdf_reader.getPage(0).extractText())

    @override_settings(DEBUG=True)
    def test_record_cannot_be_exported_by_non_owning_user(self):
        other_user = User.objects.create_user(username='other_user', password='dummy')
        report = Report.objects.create(owner=other_user, encrypted=b'first report')
        response = self.client.get(self.export_url % report.id)
        self.assertEqual(response.status_code, 403)

    @patch('callisto_core.delivery.views.PDFFullReport.generate_pdf_report')
    def test_export_exception_is_handled(self, mock_generate_pdf_report):
        mock_generate_pdf_report.side_effect = Exception('Mock Generate PDF Exception')
        response = self.client.post(
            (self.export_url % self.report.id),
            data={'key': self.report_key},
        )
        self.assertIn('There was an error exporting your report.', response.context['form'].errors['__all__'])


class DeleteRecordTest(ExistingRecordTest):

    delete_url = "/test_reports/delete/%i/"

    @override_settings(DEBUG=True)
    def test_record_cannot_be_deleted_by_non_owning_user(self):
        other_user = User.objects.create_user(username='other_user', password='dummy')
        report = Report.objects.create(owner=other_user, encrypted=b'first report')
        response = self.client.get(self.delete_url % report.id)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_key(self):
        response = self.client.get(self.delete_url % self.report.id)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delete_report.html')
        self.assertIsInstance(response.context['form'], SecretKeyForm)

    def test_delete_requires_correct_key(self):
        response = self.client.post(
            (self.delete_url % self.report.id),
            data={'key': "abracadabra"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delete_report.html')
        form = response.context['form']
        self.assertIsInstance(form, SecretKeyForm)
        self.assertContains(response, "The passphrase didn&#39;t match.")

    def test_deletes_report(self):
        self.assertEqual(Report.objects.count(), 1)
        response = self.client.post(
            (self.delete_url % self.report.id),
            data={'key': self.report_key},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get('report_deleted'))
        self.assertEqual(Report.objects.count(), 0)

    def test_delete_passes_custom_context(self):
        response = self.client.get(self.delete_url % self.report.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('custom context', get_body(response))

    @patch('callisto_core.delivery.views.Report.delete')
    def test_delete_exception_is_handled(self, mock_delete):
        mock_delete.side_effect = Exception('Mock Delete Report Exception')
        response = self.client.post(
            (self.delete_url % self.report.id),
            data={'key': self.report_key},
        )
        self.assertIn('There was an error deleting your report.', response.context['form'].errors['__all__'])
