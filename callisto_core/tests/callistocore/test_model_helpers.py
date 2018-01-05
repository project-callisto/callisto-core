from django.conf import settings
from django.test import TestCase

from callisto_core.delivery import model_helpers
from callisto_core.delivery.hashers import PBKDF2KeyHasher, make_key


class ModelHelpersTest(TestCase):
    TEST_PREFIX = "test$prefix$abcdef"
    TEST_SALT = "saltsaltsalt"
    EXPECTED_KEY = b'\x91\x05\x1a\x04\x1e\xf8D^\xfagG\x1eEA\xce\xe1\xa9\xb78<K!*l\x8bs\xa2\x0f\xd8M\x8f\x93'

    def check_salt_no_matter_with_prefix(self, salt):
        prefix = model_helpers.ensure_encode_prefix(self.TEST_PREFIX, salt)
        self.assertEqual(self.TEST_PREFIX, prefix)

    def test_ensure_encode_prefix_with_prefix(self):
        self.check_salt_no_matter_with_prefix(None)
        self.check_salt_no_matter_with_prefix(self.TEST_SALT)
        self.check_salt_no_matter_with_prefix("")

    def test_ensure_encode_prefix_bad_input(self):
        with self.assertRaises(model_helpers.EncodePrefixException):
            model_helpers.ensure_encode_prefix(None, None)

    def test_prefix_format(self):
        prefix = model_helpers.ensure_encode_prefix(None, self.TEST_SALT)
        self.assertEqual(
            "%s$%d$%s" % (
                PBKDF2KeyHasher.algorithm,
                settings.ORIGINAL_KEY_ITERATIONS,
                self.TEST_SALT,
            ),
            prefix,
        )

    def test_key_produces_repeatable_make_key_results(self):
        prefix = model_helpers.ensure_encode_prefix(None, self.TEST_SALT)
        key = make_key(prefix, '')
        self.assertEqual(self.EXPECTED_KEY, key)

    def test_key_mismatch_on_incorrect_password(self):
        prefix = model_helpers.ensure_encode_prefix(None, self.TEST_SALT)
        key = make_key(prefix, "incorrect password")
        self.assertNotEqual(self.EXPECTED_KEY, key)
