import warnings
import hashlib

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.crypto import constant_time_compare, get_random_string, pbkdf2

UNUSABLE_KEY_PREFIX = '!'       # this will never be a valid encoded hash
UNUSABLE_KEY_SUFFIX_LENGTH = 40 # number of random chars to add after UNUSABLE_KEY_PREFIX

def is_key_usable(encoded):
    if encoded is None or encoded.startswith(UNUSABLE_KEY_PREFIX):
        return False
    try:
        identify_hasher(encoded)
    except ValueError:
        return False
    return True

def get_hashers():
    hashers = []
    for hasher_path in settings.REPORT_HASHERS:
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
    
def check_key(key, encoded, setter=None, preferred='default'):
    """
    Returns a boolean of whether or not the raw key matches the three part
    encoded digest.
    """
    if key is None or not is_key_usable(encoded):
        return False

    preferred = get_hasher(preferred)
    hasher = identify_hasher(encoded)

    hasher_changed = hasher.algorithm != preferred.algorithm
    must_update = hasher_changed or preferred.must_update(key)
    is_correct = hasher.verify(key, encoded)

    if not is_correct and not hasher_changed and must_update:
        hasher.harden_runtime(key, encoded)

    if setter and is_correct and must_update:
        setter(key)

    return is_correct

def identify_hasher(encoded):
    # assume all previous entries before this scheme is implemented use PBKDF2 + SHA256
    if len(encoded) == 32 and '$' not in encoded:
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
        stretched_key = pbkdf2(key, salt, iterations, self.digest)
        return "{0}${1}${2}${3}${4}".format(self.algorithm, iterations, salt, stretched_key)

    def verify(self, key, encoded):
        algorithm, iterations, salt, stretched_key = encoded.split('$', 3)
        assert algorithm == self.algorithm
        encoded_2 = self.encode(key, salt, int(iterations))
        return constant_time_compare(encoded, encoded_2)

    def must_update(self, encoded):
        algorithm, iterations, salt, stretched_key = encoded.split('$', 3)
        return int(iterations) != self.iterations

    def harden_runtime(self, key, encoded):
        algorithm, iterations, salt, stretched_key = encoded.split('$', 3)
        extra_iterations = self.iterations - int(iterations)
        if extra_iterations > 0:
            self.encode(key, salt, extra_iterations)

class Argon2KeyHasher(BaseKeyHasher):
    algorithm = 'argon2'

    time_cost = settings.ARGON2_TIME_COST
    memory_cost = settings.ARGON2_MEM_COST
    parallelism = settings.ARGON2_PARALLELISM

    def encode(self, key, salt):
        data = argon2.low_level.hash_secret(
            force_bytes(key),
            force_bytes(salt),
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
            hash_len=argon2.DEFAULT_HASH_LENGTH,
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
