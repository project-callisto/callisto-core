from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site


class NewReportFlowTest(TestCase):

    report_key = 'super secret'

    fixtures = [
        'wizard_builder_data',
    ]

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()

    def test_report_creation_redirects_to_wizard_view(self):
        response = self.client.post(
            reverse('report_new'),
            data={
                'key': self.report_key,
                'key_confirmation': self.report_key,
            },
            follow=True,
        )
        uuid = response.context['report'].uuid
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse('wizard_update', kwargs={'step':0,'uuid':uuid}),
        )

    def test_report_creation_access_key_to_session(self):
        pass

    def test_access_form_rendered_when_no_key_in_session(self):
        pass
