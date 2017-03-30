# django
from django_migration_testcase import MigrationTest

# local
from callisto.notification.models import EmailNotification


class EmailNotificationMigrationTest(MigrationTest):

    before = [('delivery', '0009_to_address_to_textfield'), ('notification', '0001_initial')]
    after = [('delivery', '0010_delete_emailnotification'), ('notification', '0002_populate_email_notification')]

    def test_email_notication_migration(self):

        name = 'migration_test'
        subject = 'migration test'
        body = 'test for email notification migration'

        EmailNotificationOld = self.get_model_before('delivery.EmailNotification')
        EmailNotificationOld.objects.create(
            name=name,
            subject=subject,
            body=body,
        )

        self.run_migration()

        EmailNotificationNew = self.get_model_after('notification.EmailNotification')
        email_notifcation_new, created = EmailNotificationNew.objects.get_or_create(
            name=name,
            subject=subject,
            body=body,
        )

        self.assertFalse(created)
