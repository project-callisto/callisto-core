from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from callisto_core.delivery.forms import ReportAccessForm, ReportCreateForm
from wizard_builder.forms import PageForm


class ReportFlowHelper(TestCase):

    secret_key = 'super secret'
    fixtures = [
        'wizard_builder_data',
    ]

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()

    def client_post_report_creation(self):
        return self.client.post(
            reverse('report_new'),
            data={
                'key': self.secret_key,
                'key_confirmation': self.secret_key,
            },
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
        self.assertIsInstance(form, ReportCreateForm)

    def test_report_creation_redirects_to_wizard_view(self):
        response = self.client_post_report_creation()
        uuid = response.context['report'].uuid
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse('wizard_update', kwargs={'step':0,'uuid':uuid}),
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
        self.client_clear_secret_key()

        response = self.client.get(
            reverse('wizard_update', kwargs={'step':0,'uuid':uuid}))
        form = response.context['form']

        self.assertIsInstance(form, ReportAccessForm)

    def test_can_reenter_secret_key(self):
        response = self.client_post_report_creation()
        uuid = response.context['report'].uuid
        self.client_clear_secret_key()

        response = self.client_post_report_access(
            response.redirect_chain[0][0])
        form = response.context['form']

        self.assertIsInstance(form, PageForm)

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
        self.assertIsInstance(form, ReportAccessForm)
