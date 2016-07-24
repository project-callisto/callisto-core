import base64

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes

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


class PBKDF2KeyHasherTest(TestCase):

    def setUp(self):
        self.hasher = hashers.PBKDF2KeyHasher()

    def test_encode_requires_key_and_salt(self):
        with self.assertRaises(AssertionError):
            self.hasher.encode(None, None)
            self.hasher.encode("key", None)
            self.hasher.encode(None, "salt")
            self.hasher.encode("key", "salt$")

    def test_encode_returns_correct_prefix(self):
        encoded = self.hasher.encode("this is definitely a key", "also here is a salt", iterations=142)
        prefix = encoded.rsplit('$', 1)[0]
        expected = "pbkdf2_sha256$142$also here is a salt"
        self.assertEqual(prefix, expected)

    def test_must_update_on_different_iterations(self):
        prefix = "pbkdf2_sha256${0}$thisisasalt"
        prefix_less = prefix.format(settings.KEY_ITERATIONS - 5)
        prefix_more = prefix.format(settings.KEY_ITERATIONS + 5)
        prefix_same = prefix.format(settings.KEY_ITERATIONS)
        self.assertTrue(self.hasher.must_update(prefix_less))
        self.assertTrue(self.hasher.must_update(prefix_more))
        self.assertFalse(self.hasher.must_update(prefix_same))

    def test_verify_encoded(self):
        encoded = self.hasher.encode("this is definitely a key", "yup that's salt")
        correct = self.hasher.verify("this is definitely a key", encoded)
        incorrect = self.hasher.verify("this is definitely not the right key", encoded)
        self.assertTrue(correct)
        self.assertFalse(incorrect)


class Argon2KeyHasherTest(TestCase):

    def setUp(self):
        self.hasher = hashers.Argon2KeyHasher()

    def test_encode_requires_key_and_salt(self):
        with self.assertRaises(AssertionError):
            self.hasher.encode(None, None)
            self.hasher.encode("key", None)
            self.hasher.encode(None, "salt")
            self.hasher.encode("key", "salt$")

    def test_encode_returns_correct_prefix(self):
        encoded = self.hasher.encode("this is definitely a key", "also here is a salt")
        prefix = encoded.rsplit('$', 1)[0]
        b64_salt = base64.b64encode(force_bytes("also here is a salt")).decode('utf-8').rstrip('=')
        expected = "argon2$argon2i$v=19$m=512,t=2,p=2${0}".format(b64_salt)
        self.assertEqual(prefix, expected)

    def test_verify_encoded(self):
        encoded = self.hasher.encode("this is definitely a key", "wow that's salty")
        correct = self.hasher.verify("this is definitely a key", encoded)
        incorrect = self.hasher.verify("nope this isn't the key idk what this is", encoded)
        self.assertTrue(correct)
        self.assertFalse(incorrect)

    def test_split_encoded_returns_correct_prefix(self):
        encoded = self.hasher.encode("this is definitely a key", "also here is a salt")
        prefix, stretched = self.hasher.split_encoded(encoded)
        expected = "argon2$argon2i$v=19$m=512,t=2,p=2$also here is a salt"
        self.assertEqual(prefix, expected)
