from config.tests.base import CallistoTestCase

from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(CallistoTestCase):

    def setUp(self):
        super().setUp()
        self.user = self.create_user(
            username="dummy",
            password="dummy",
            email="dummy@dummy.com")

    def test_can_save_email(self):
        self.assertEqual(
            User.objects.get(
                username="dummy").email,
            "dummy@dummy.com")

    def test_email_is_optional(self):
        user = self.create_user(username="dummy2", password="dummy")
        self.assertEqual(User.objects.get(username="dummy2"), user)
        self.assertEqual(User.objects.get(username="dummy2").email, '')

    def test_can_set_fields_on_account(self):
        self.user.account.school_email = "test@example.com"
        self.user.account.save()
        self.assertEqual(
            User.objects.get(
                username="dummy").account.school_email,
            "test@example.com")
