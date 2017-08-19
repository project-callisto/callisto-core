from unittest import skip

from callisto_core.delivery.models import Report
from callisto_core.notification.models import EmailNotification
from mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from .. import test_base

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


class SiteIDTest(test_base.ReportFlowHelper):

    def setUp(self):
        super().setUp()
        self.second_site = Site.objects.create(domain='generic_second_site')

    @override_settings()
    def test_on_site_respects_SITE_ID_setting(self):
        site_1 = Site.objects.get(id=1)
        site_2 = Site.objects.create()
        site_1_pages = 3
        site_2_pages = site_1_pages + 1

        index = 0
        for i in range(site_1_pages):
            notification = EmailNotification.objects.create(name=index)
            notification.sites.add(site_1)
            index += 1
        for i in range(site_2_pages):
            notification = EmailNotification.objects.create(name=index)
            notification.sites.add(site_2)
            index += 1

        with TempSiteID(site_1.id):
            self.assertEqual(EmailNotification.objects.on_site().count(), site_1_pages)

        with TempSiteID(site_2.id):
            self.assertEqual(EmailNotification.objects.on_site().count(), site_2_pages)

    @override_settings()
    def test_site_not_overriden_on_save(self):
        site = Site.objects.create()
        # site_id will be a string on live, since its an environment variable
        site_id = str(site.id)
        with TempSiteID(site_id):
            email = EmailNotification.objects.create(name='test_name')
            email.sites.add(2)
            email.save()
        self.assertEqual(email.sites.count(), 1)
        self.assertNotEqual(email.sites.first().id, site_id)
        self.assertEqual(email.sites.first().id, self.second_site.id)

    @override_settings()
    def test_multiple_added_sites_are_reflected_by_on_site(self):
        site_2 = Site.objects.create()
        notification = EmailNotification.objects.create()
        notification.sites.add(1)
        notification.sites.add(site_2)

        with TempSiteID(1):
            self.assertIn(notification, EmailNotification.objects.on_site())

        with TempSiteID(site_2.id):
            self.assertIn(notification, EmailNotification.objects.on_site())


class SiteRequestTest(TestCase):

    @skip('temporariy disabled')
    def test_can_request_pages_without_site_id_set(self):
        self.client_post_report_creation()
        response = self.client_post_reporting()
        self.assertNotEqual(response.status_code, 404)

    @skip('temporariy disabled')
    @patch('callisto_core.notification.managers.EmailNotificationQuerySet.on_site')
    def test_site_passed_to_email_notification_manager(self, mock_on_site):
        self.client_post_report_creation()
        self.client_post_reporting()
        mock_on_site.assert_called_with(self.site.id)
