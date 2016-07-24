import base64
import hashlib
import warnings

import argon2

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import (
    constant_time_compare, get_random_string, pbkdf2,
)
from django.utils.encoding import force_bytes
from django.utils.module_loading import import_string


def get_hashers():
    hashers = []
    for hasher_path in settings.KEY_HASHERS:
        hasher_cls = import_string(hasher_path)
        hasher = hasher_cls()
        if not getattr(hasher, 'algorithm'):
            raise ImproperlyConfigured("hasher doesn't specify an algorithm name: {}".format(hasher_path))
        hashers.append(hasher)
    return hashers


def get_hashers_by_algorithm():
    hashers = get_hashers()
    return {hasher.algorithm: hasher for hasher in hashers}


def get_hasher(algorithm='default'):
    if algorithm == 'default':
        return get_hashers()[0]
    else:
        hashers = get_hashers_by_algorithm()
        try:
            return hashers[algorithm]
        except KeyError:
            raise ValueError("Unknown key hashing algorithm {0}."
                             "Did you specify it in the KEY_HASHERS setting?".format(algorithm))


def identify_hasher(encoded):
    """
    Returns a hasher based on either a fully encoded key or just the encode
    prefix. If the encoded prefix is empty, assume the previous default hasher.
    """
    # assume all previous entries before this scheme is implemented use PBKDF2 + SHA256
    if not encoded:
        algorithm = 'pbkdf2_sha256'
    else:
        algorithm = encoded.split('$', 1)[0]
    return get_hasher(algorithm)


class BaseKeyHasher(object):
    """
    Abstract base class for key hashers based on django password hashers.

    New hashers must override algorithm, verify(), and encode().
    """
    algorithm = None

    def salt(self):
        return get_random_string()

    def verify(self, key, encoded):
        raise NotImplementedError('subclasses of BaseKeyHasher must provide a verify() method')

    def encode(self, key, salt):
        raise NotImplementedError('subclasses of BaseKeyHasher must provide a encode() method')

    def harden_runtime(self, key, encoded):
        warnings.warn('subclasses of BaseKeyHasher should provide a harden_runtime() method')


class PBKDF2KeyHasher(BaseKeyHasher):
    algorithm = 'pbkdf2_sha256'
    iterations = settings.KEY_ITERATIONS
    digest = hashlib.sha256

    def encode(self, key, salt, iterations=None):
        assert key is not None
        assert salt and '$' not in salt
        if not iterations:
            iterations = self.iterations
        iterations = int(iterations)
        stretched_key = pbkdf2(key, salt, iterations, digest=self.digest)
        stretched_key = base64.b64encode(stretched_key).decode('utf-8')
        return "{0}${1}${2}${3}".format(self.algorithm, iterations, salt, stretched_key)

    def verify(self, key, encoded):
        algorithm, iterations, salt, stretched_key = encoded.split('$', 3)
        assert algorithm == self.algorithm
        encoded_2 = self.encode(key, salt, int(iterations))
        return constant_time_compare(encoded, encoded_2)

    def must_update(self, encode_prefix):
        algorithm, iterations, salt = encode_prefix.split('$', 2)
        return int(iterations) != self.iterations

    def harden_runtime(self, key, encoded):
        algorithm, iterations, salt, stretched_key = encoded.split('$', 3)
        extra_iterations = self.iterations - int(iterations)
        if extra_iterations > 0:
            self.encode(key, salt, extra_iterations)

    def split_encoded(self, encoded):
        """
        Splits the encoded string into a separate prefix and stretched key.

        Returns a prefix and a stretched key.
        """
        prefix, b64stretched = encoded.rsplit('$', 1)
        stretched_key = base64.b64decode(b64stretched)
        return prefix, force_bytes(stretched_key)


class Argon2KeyHasher(BaseKeyHasher):
    algorithm = 'argon2'

    time_cost = settings.ARGON2_TIME_COST
    memory_cost = settings.ARGON2_MEM_COST
    parallelism = settings.ARGON2_PARALLELISM

    # accept **kwargs to allow a single encode statement across different hashers
    def encode(self, key, salt, **kwargs):
        assert key is not None
        assert salt and '$' not in salt
        data = argon2.low_level.hash_secret(
            force_bytes(key),
            force_bytes(salt),
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
            hash_len=32,
            type=argon2.low_level.Type.I,
        )
        return self.algorithm + data.decode('utf-8')

    def verify(self, key, encoded):
        algorithm, rest = encoded.split('$', 1)
        assert algorithm == self.algorithm
        try:
            return argon2.low_level.verify_secret(
                force_bytes('$' + rest),
                force_bytes(key),
                type=argon2.low_level.Type.I,
            )
        except argon2.exceptions.VerificationError:
            return False

    def must_update(self, encoded):
        (algorithm, variety, version, time_cost, memory_cost, parallelism,
            salt, data) = self._decode(encoded)
        assert algorithm == self.algorithm
        return (
            argon2.low_level.ARGON2_VERSION != version or
            self.time_cost != time_cost or
            self.memory_cost != memory_cost or
            self.parallelism != parallelism
        )

    def split_encoded(self, encoded):
        """
        Splits the encoded string into a separate prefix and stretched key.
        Also decodes the salt and key from base64 encoding automatically done by argon2.low_level.secret_hash().

        Returns a prefix and a stretched key.
        """
        prefix_minus_salt, b64salt, b64stretched = encoded.rsplit('$', 2)
        missing_padding_salt = 4 - len(b64salt) % 4
        missing_padding_hash = 4 - len(b64stretched) % 4

        # argon2's secret_hash() output doesn't include padding so to decode it we have to add it back in
        if missing_padding_hash:
            b64stretched += '=' * missing_padding_hash
        if missing_padding_salt:
            b64salt += '=' * missing_padding_salt

        stretched_key = base64.b64decode(b64stretched)

        salt = base64.b64decode(b64salt).decode('utf-8').rstrip('=')
        prefix = "$".join((prefix_minus_salt, salt))
        return prefix, stretched_key

    def _decode(self, encoded):
        """
        Split an encoded hash and return: (
            algorithm, variety, version, time_cost, memory_cost,
            parallelism, salt, data,
        ).
        """
        bits = encoded.split('$')
        if len(bits) == 5:
            # Argon2 < 1.3
            algorithm, variety, raw_params, salt, data = bits
            version = 0x10
        else:
            assert len(bits) == 6
            algorithm, variety, raw_version, raw_params, salt, data = bits
            assert raw_version.startswith('v=')
            version = int(raw_version[len('v='):])
        params = dict(bit.split('=', 1) for bit in raw_params.split(','))
        assert len(params) == 3 and all(x in params for x in ('t', 'm', 'p'))
        time_cost = int(params['t'])
        memory_cost = int(params['m'])
        parallelism = int(params['p'])
        return (
            algorithm, variety, version, time_cost, memory_cost, parallelism,
            salt, data,
            )
