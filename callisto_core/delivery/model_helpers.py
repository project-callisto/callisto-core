import json

import gnupg

from django.conf import settings
from django.contrib.auth.hashers import PBKDF2PasswordHasher


class EncodePrefixException(BaseException):
    pass


def salt_to_encode_prefix(salt):
    iterations = settings.ORIGINAL_KEY_ITERATIONS
    return "%s$%d$%s" % (PBKDF2PasswordHasher.algorithm, iterations, salt)


def ensure_encode_prefix(encode_prefix, salt):
    if not encode_prefix and not salt:
        raise EncodePrefixException
    elif not encode_prefix:
        return salt_to_encode_prefix(salt)
    else:
        return encode_prefix


def gpg_encrypt_data(data, key):
    data_string = json.dumps(data)
    gpg = gnupg.GPG()
    imported_keys = gpg.import_keys(key)
    encrypted = gpg.encrypt(
        data_string,
        imported_keys.fingerprints[0],
        armor=True,
        always_trust=True)
    return encrypted.data
