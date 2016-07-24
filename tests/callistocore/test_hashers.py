from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

import callisto.delivery.hashers as hashers


class BaseKeyHasherTest(TestCase):

    def setUp(self):
        self.hasher = hashers.BaseKeyHasher()

    def test_base_class_algorithm_is_none(self):
        self.assertIsNone(self.hasher.algorithm)

    @override_settings(KEY_HASHERS=['callisto.delivery.hashers.BaseKeyHasher'])
    def test_get_hashers_raises_improperly_configured_for_no_algorithm(self):
        with self.assertRaises(ImproperlyConfigured) as cm:
            hashers.get_hashers()
        ex = cm.exception
        self.assertEqual(str(ex), "hasher doesn't specify an algorithm name: callisto.delivery.hashers.BaseKeyHasher")

    def test_get_hashers_returns_correct_hashers(self):
        hs = hashers.get_hashers()
        self.assertIsInstance(hs[0], hashers.Argon2KeyHasher)
        self.assertIsInstance(hs[1], hashers.PBKDF2KeyHasher)

    def test_get_hasher_returns_correct_hasher(self):
        hs = []
        hs.append(hashers.get_hasher())                 # argon2
        hs.append(hashers.get_hasher("argon2"))         # argon2
        hs.append(hashers.get_hasher("pbkdf2_sha256"))  # pbkdf2
        self.assertIsInstance(hs.pop(), hashers.PBKDF2KeyHasher)
        self.assertIsInstance(hs.pop(), hashers.Argon2KeyHasher)
        self.assertIsInstance(hs.pop(), hashers.Argon2KeyHasher)

    def test_get_hasher_raises_ValueError_on_unknown_algorithm(self):
        with self.assertRaises(ValueError) as cm:
            hashers.get_hasher("sha420_8^)")
        ex = cm.exception
        self.assertEqual(str(ex), "Unknown key hashing algorithm sha420_8^)."
                                  "Did you specify it in the KEY_HASHERS setting?")

    def test_identify_hasher_returns_correct_hashers(self):
        hs = []
        hs.append(hashers.identify_hasher(None))                                    # pbkdf2
        hs.append(hashers.identify_hasher("pbkdf2_sha256$100$a_salt_probably"))     # pbkdf2
        hs.append(hashers.identify_hasher("argon2$argon2i$v=19$more,params$salt"))  # argon2
        self.assertIsInstance(hs.pop(), hashers.Argon2KeyHasher)
        self.assertIsInstance(hs.pop(), hashers.PBKDF2KeyHasher)
        self.assertIsInstance(hs.pop(), hashers.PBKDF2KeyHasher)
