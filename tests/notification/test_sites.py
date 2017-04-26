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
        self.site_id_stable = getattr(settings, 'SITE_ID', 1)
        settings.SITE_ID = self.site_id_temp

    def __exit__(self, *args):
        settings.SITE_ID = self.site_id_stable


class SiteIDTest(TestCase):

    def test_on_site_respects_SITE_ID_setting(self):
        site_1_pages = 3
        site_2_pages = site_1_pages + 1
        site_2 = Site.objects.create()
        index = 0
        for i in range(site_1_pages):
            EmailNotification.objects.create(name=index)
            index += 1
        for i in range(site_2_pages):
            notification = EmailNotification.objects.create(name=index)
            notification.sites.add(site_2)  # site_1 is already added
            index += 1

        self.assertEqual(EmailNotification.objects.on_site().count(), site_1_pages + site_2_pages)
        with TempSiteID(site_2.id):
            self.assertEqual(EmailNotification.objects.on_site().count(), site_2_pages)

    def test_site_not_added_multiple_times_on_save(self):
        with TempSiteID('2'):
            email = EmailNotification.objects.create(name='test_name')
            email.save()
            email.save()
        self.assertEqual(email.sites.count(), 1)

    def test_multiple_added_sites_are_reflected_by_on_site(self):
        site_2 = Site.objects.create()
        notification = EmailNotification.objects.create()
        notification.sites.add(site_2)

        self.assertIn(notification, EmailNotification.objects.on_site())
        with TempSiteID(site_2.id):
            self.assertIn(notification, EmailNotification.objects.on_site())


class SiteRequestTest(TestCase):

    def setUp(self):
        super(SiteRequestTest, self).setUp()
        User.objects.create_user(username='dummy', password='dummy')
        self.client.login(username='dummy', password='dummy')
        user = User.objects.get(username='dummy')
        self.report = Report(owner=user)
        self.report_key = 'bananabread! is not my key'
        self.report.encrypt_report('{}', self.report_key)
        self.report.save()
        self.submit_url = reverse('test_submit_report', args=[self.report.pk])

    @override_settings()
    @patch('django.http.request.HttpRequest.get_host')
    def test_can_request_pages_without_site_id_set(self, mock_get_host):
        mock_get_host.return_value = Site.objects.get(id=settings.SITE_ID).domain
        del settings.SITE_ID
        response = self.client.get(self.submit_url)
        self.assertNotEqual(response.status_code, 404)

    @override_settings()
    @patch('django.http.request.HttpRequest.get_host')
    @patch('callisto.notification.managers.EmailNotificationQuerySet.on_site')
    def test_site_passed_to_email_notification_manager(self, mock_on_site, mock_get_host):
        mock_get_host.return_value = Site.objects.get(id=settings.SITE_ID).domain
        site_id = settings.SITE_ID
        del settings.SITE_ID
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
        mock_on_site.assert_called_with(site_id)
