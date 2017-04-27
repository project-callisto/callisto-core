from django.core.exceptions import ValidationError
from django.test import TestCase

from callisto.notification.models import EmailNotification


class EmailValidationTest(TestCase):

    def test_duplicate_emails_not_allowed(self):
        with self.assertRaises(ValidationError):
            for i in range(2):
                email = EmailNotification.objects.create(
                    name='example email'
                )
                email.sites.add(1)
                email.full_clean()
        self.assertEqual(EmailNotification.objects.count(), 1)
