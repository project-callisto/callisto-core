from unittest import skip

from django_migration_testcase import MigrationTest


class EmailNotificationDeliveryMigrationTest(MigrationTest):

    before = [("delivery", "0009_to_address_to_textfield"), ("notification", "zero")]
    after = [
        ("delivery", "0010_email_notification_data_migration"),
        ("notification", "0001_initial_create_email_notification"),
    ]

    @skip("migration already run")
    def test_email_notication_migration(self):

        name = "migration_test"
        subject = "migration test"
        body = "test for email notification migration"

        LegacyEmailNotification = self.get_model_before("delivery.EmailNotification")
        LegacyEmailNotification.objects.create(name=name, subject=subject, body=body)
        self.assertEqual(LegacyEmailNotification.objects.count(), 1)

        self.run_migration()

        NewEmailNotification = self.get_model_after("notification.EmailNotification")
        _, created = NewEmailNotification.objects.get_or_create(
            name=name, subject=subject, body=body
        )

        self.assertFalse(created)
        self.assertEqual(NewEmailNotification.objects.count(), 1)


class EmailNotificationPKTest(MigrationTest):

    app_name = "notification"
    before = "0002_emailnotification_sites"
    after = "0005_rename_to_emailnotification"

    @skip("migration already run")
    def test_email_notication_primary_key_creation(self):

        name = "migration_test"
        subject = "migration test"
        body = "test for email notification migration"

        LegacyEmailNotification = self.get_model_before("EmailNotification")
        LegacyEmailNotification.objects.create(name=name, subject=subject, body=body)
        self.assertEqual(LegacyEmailNotification.objects.count(), 1)

        self.run_migration()

        NewEmailNotification = self.get_model_after("EmailNotification")
        email, created = NewEmailNotification.objects.get_or_create(
            name=name, subject=subject, body=body
        )

        self.assertFalse(created)
        self.assertIsInstance(email.id, int)
        self.assertEqual(NewEmailNotification.objects.count(), 1)
