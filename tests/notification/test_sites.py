from mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from callisto.delivery.models import Report
from callisto.notification.models import EmailNotification

User = get_user_model()


class TempSiteID():
    '''
        with TempSiteID(1):
            ...
    '''

    def __init__(self, site_id):
        self.site_id_temp = site_id

    def __enter__(self):
        self.site_id_stable = getattr(settings, 'SITE_ID', None)
        settings.SITE_ID = self.site_id_temp

    def __exit__(self, *args):
        settings.SITE_ID = self.site_id_stable


class SiteIDTest(TestCase):

    @override_settings()
    def test_on_site_respects_SITE_ID_setting(self):
        site_1_pages = 3
        site_2_pages = site_1_pages + 1
        with TempSiteID(1):
            site_2 = Site.objects.create()
            index = 0
            for i in range(site_1_pages):
                EmailNotification.objects.create(name=index)
                index += 1
            for i in range(site_2_pages):
                notification = EmailNotification.objects.create(name=index)
                notification.sites.add(site_2)
                index += 1
            self.assertEqual(EmailNotification.objects.on_site().count(), site_1_pages + site_2_pages)

        with TempSiteID(site_2.id):
            self.assertEqual(EmailNotification.objects.on_site().count(), site_2_pages)

    @override_settings()
    def test_site_not_added_multiple_times_on_save(self):
        site = Site.objects.create()
        # site_id will be a string on live, since its an environment variable
        site_id = str(site.id)
        with TempSiteID(site_id):
            email = EmailNotification.objects.create(name='test_name')
            email.save()
            email.save()
        self.assertEqual(email.sites.count(), 1)

    @override_settings()
    def test_multiple_added_sites_are_reflected_by_on_site(self):
        with TempSiteID(1):
            site_2 = Site.objects.create()
            notification = EmailNotification.objects.create()
            notification.sites.add(site_2)
            self.assertIn(notification, EmailNotification.objects.on_site())

        with TempSiteID(site_2.id):
            self.assertIn(notification, EmailNotification.objects.on_site())


class SiteRequestTest(TestCase):

    def setUp(self):
        super(SiteRequestTest, self).setUp()
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()
        User.objects.create_user(username='dummy', password='dummy')
        self.client.login(username='dummy', password='dummy')
        user = User.objects.get(username='dummy')
        self.report = Report(owner=user)
        self.report_key = 'bananabread! is not my key'
        self.report.encrypt_report('{}', self.report_key)
        self.report.save()
        self.submit_url = reverse('test_submit_report', args=[self.report.pk])

    def test_can_request_pages_without_site_id_set(self):
        response = self.client.get(self.submit_url)
        self.assertNotEqual(response.status_code, 404)

    @patch('callisto.notification.managers.EmailNotificationQuerySet.on_site')
    def test_site_passed_to_email_notification_manager(self, mock_on_site):
        self.client.post(
            self.submit_url,
            data={
                'name': 'test submitter',
                'email': 'test@example.com',
                'phone_number': '555-555-1212',
                'email_confirmation': 'True',
                'key': self.report_key,
            },
        )
        mock_on_site.assert_called_with(self.site.id)
