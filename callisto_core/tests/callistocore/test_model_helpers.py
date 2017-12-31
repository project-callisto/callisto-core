from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.test import TestCase

from callisto_core.delivery import model_helpers


class ModelHelpersTest(TestCase):
    TEST_PREFIX = "test_prefix"
    TEST_SALT = "239823ADEF3"

    def check_salt_no_matter_with_prefix(self, salt):
        pre = model_helpers.ensure_encode_prefix(self.TEST_PREFIX, salt)
        self.assertEqual(self.TEST_PREFIX, pre, "Unexpected prefix returned")

    def test_ensure_encode_prefix_with_prefix(self):
        self.check_salt_no_matter_with_prefix(None)
        self.check_salt_no_matter_with_prefix(self.TEST_SALT)
        self.check_salt_no_matter_with_prefix("")

    def test_ensure_encode_prefix_bad_input(self):
        with self.assertRaises(model_helpers.EncodePrefixException):
            model_helpers.ensure_encode_prefix(None, None)

    def test_ensure_encode_prefix_only_salt(self):
        pre = model_helpers.ensure_encode_prefix(
            None,
            self.TEST_SALT
        )
        self.assertEqual(pre, "pbkdf2_sha256$100000$" + self.TEST_SALT)
