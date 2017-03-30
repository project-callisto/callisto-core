# django
from django_migration_testcase import MigrationTest


class EmailNotificationMigrationTest(MigrationTest):

    before = [('delivery', '0010_rename_email_notification'), ('notification', 'zero')]
    after = [('delivery', '0011_email_notification_data_migration'), ('notification', '0001_initial_create_email_notification')]

    def test_email_notication_migration(self):

        name = 'migration_test'
        subject = 'migration test'
        body = 'test for email notification migration'

        LegacyEmailNotificationBefore = self.get_model_before('delivery.LegacyEmailNotification')
        LegacyEmailNotificationBefore.objects.create(
            name=name,
            subject=subject,
            body=body,
        )
        self.assertEqual(LegacyEmailNotificationBefore.objects.count(), 1)

        self.run_migration()

        LegacyEmailNotificationAfter = self.get_model_after('delivery.LegacyEmailNotification')
        NewEmailNotification = self.get_model_after('notification.EmailNotification')
        _, created = NewEmailNotification.objects.get_or_create(
            name=name,
            subject=subject,
            body=body,
        )

        self.assertFalse(created)
        self.assertEqual(NewEmailNotification.objects.count(), 1)
