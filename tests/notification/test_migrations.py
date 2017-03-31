# django
from django_migration_testcase import MigrationTest


class EmailNotificationMigrationTest(MigrationTest):

    before = [
        ('delivery', '0009_to_address_to_textfield'),
        ('notification', 'zero'),
    ]
    after = [
        ('delivery', '0010_email_notification_data_migration'),
        ('notification', '0001_initial_create_email_notification'),
    ]

    def test_email_notication_migration(self):

        name = 'migration_test'
        subject = 'migration test'
        body = 'test for email notification migration'

        LegacyEmailNotification = self.get_model_before('delivery.EmailNotification')
        LegacyEmailNotification.objects.create(
            name=name,
            subject=subject,
            body=body,
        )
        self.assertEqual(LegacyEmailNotification.objects.count(), 1)

        self.run_migration()

        NewEmailNotification = self.get_model_after('notification.EmailNotification')
        _, created = NewEmailNotification.objects.get_or_create(
            name=name,
            subject=subject,
            body=body,
        )

        self.assertFalse(created)
        self.assertEqual(NewEmailNotification.objects.count(), 1)
