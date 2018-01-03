import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from callisto_core.utils.api import NotificationApi

User = get_user_model()
logger = logging.getLogger(__name__)


class Account(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4)
    is_verified = models.BooleanField(default=False)
    school_email = models.EmailField(blank=True)
    invalid = models.BooleanField(default=False)
    site_id = models.PositiveSmallIntegerField(blank=False)


class BulkAccount(models.Model):
    emails = models.TextField()
    site_id = models.PositiveSmallIntegerField(blank=False)

    def create_accounts(self):
        emails = self.emails.split(',')
        NotificationApi.slack_notification(
            f'Running bulk account creation for {len(emails)} accounts',
            channel='#launch'
        )

        emails = [
            email.strip().lower()
            for email in emails
            if email
        ]
        self.parsed_emails = emails
        logger.debug(self.parsed_emails)

        for email in emails:
            user, user_created = User.objects.get_or_create(
                username=email,
            )
            if user_created:
                user.set_password(User.objects.make_random_password())
                user.save()
            User.objects.filter(id=user.id).update(
                email=email,
            )

            account, _ = Account.objects.get_or_create(
                user_id=user.id,
            )
            Account.objects.filter(id=account.id).update(
                is_verified=True,
                school_email=email,
                site_id=self.site_id,
            )

            NotificationApi.send_account_activation_email(user, email)

    def save(self, *args, **kwargs):
        self.create_accounts()

    class Meta:
        managed = False
        verbose_name = 'Bulk Account'
