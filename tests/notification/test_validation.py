from tests.notification.test_sites import TempSiteID

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from callisto.notification.models import EmailNotification


class EmailValidationTest(TestCase):

    @override_settings()
    def setUp(self):
        del settings.SITE_ID
        self.populate_sites()
        self.populate_emails()
        super(EmailValidationTest, self).setUp()

    def populate_sites(self):
        for i in range(1, 10):
            site, _ = Site.objects.get_or_create(
                id=i,
            )
            site.domain = str(i)
            site.save()

    def populate_emails(self):
        for i in range(1, 10):
            email, _ = EmailNotification.objects.get_or_create(
                name='example email',
                body='example email',
                subject='example email',
                sites__id__in=[i]
            )
            email.sites.add(i)
            email.full_clean()

    def test_validation_error_does_not_delete_email(self):
        with self.assertRaises(ValidationError):
            invalid_email = EmailNotification.objects.get(
                name='example email',
                sites__id__in=[1],
            )
            invalid_email.sites.add(2)
            invalid_email.full_clean()
        self.assertTrue(invalid_email.pk)

    def test_duplicate_emails_not_allowed_on_same_site(self):
        site_id = 1
        with self.assertRaises(ValidationError):
            for i in range(10):
                email = EmailNotification.objects.create(
                    name='example email',
                    body='example email',
                    subject='example email',
                )
                email.sites.add(site_id)
                email.full_clean()
        self.assertEqual(EmailNotification.objects.on_site(site_id).count(), 1)

    def test_cannot_add_site_which_would_create_duplicate(self):
        with self.assertRaises(ValidationError):
            email = EmailNotification.objects.get(
                name='example email',
                sites__id__in=[1],
            )
            email.sites.add(2)
            email.full_clean()
        self.assertEqual(EmailNotification.objects.on_site(2).count(), 1)

    def test_validation_error_contains_identifying_information(self):
        email_name = 'example email'
        invalid_site = 2
        with self.assertRaises(ValidationError) as error_context:
            email = EmailNotification.objects.get(
                name=email_name,
                sites__id__in=[1],
            )
            email.sites.add(invalid_site)
            email.full_clean()
        exception_text = str(error_context.exception)
        self.assertIn(email_name, exception_text)
        self.assertIn(str(invalid_site), exception_text)

    def test_all_duplicate_sites_removed(self):
        with self.assertRaises(ValidationError):
            email_with_invalid_sites = EmailNotification.objects.get(
                name='example email',
                sites__id__in=[1],
            )
            email_with_invalid_sites.sites.add(2)
            email_with_invalid_sites.sites.add(3)
            email_with_invalid_sites.full_clean()
        self.assertEqual(email_with_invalid_sites.sites.count(), 1)
        self.assertEqual(EmailNotification.objects.on_site(2).count(), 1)
        self.assertEqual(EmailNotification.objects.on_site(3).count(), 1)


class EmailSiteIDValidationTest(EmailValidationTest):

    @override_settings()
    def test_site_only_added_when_no_default_set(self):
        email = EmailNotification.objects.create(
            name='example email',
            body='example email',
            subject='example email',
        )
        email.sites.add(1)

        with TempSiteID(2):
            email.save()

        self.assertEqual(email.sites.count(), 1)
