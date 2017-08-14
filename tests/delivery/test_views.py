from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from callisto_core.delivery.forms import ReportAccessForm, ReportCreateForm
from wizard_builder.forms import PageForm


class NewReportFlowTest(TestCase):

    report_key = 'super secret'

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
                'key': self.report_key,
                'key_confirmation': self.report_key,
            },
            follow=True,
        )

    def clear_secret_key(self):
        session = self.client.session
        session['secret_key'] = None
        session.save()
        self.assertEqual(
            self.client.session.get('secret_key'),
            None,
        )

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
            self.report_key,
        )

    def test_access_form_rendered_when_no_key_in_session(self):
        response = self.client_post_report_creation()
        uuid = response.context['report'].uuid
        self.clear_secret_key()

        response = self.client.get(
            reverse('wizard_update', kwargs={'step':0,'uuid':uuid}))
        form = response.context['form']

        self.assertIsInstance(form, ReportAccessForm)
