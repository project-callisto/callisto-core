import json

import gnupg

from django.conf import settings

from callisto_core.delivery.hashers import PBKDF2KeyHasher


class EncodePrefixException(BaseException):
    pass


UNUSED_PREFIX_PASSWORD = "unused in prefix"


def salt_to_encode_prefix(salt):
    # form PBKDF2 prefix and key from the library and then return only the prefix
    hasher = PBKDF2KeyHasher()
    enc = hasher.encode(UNUSED_PREFIX_PASSWORD, salt, settings.ORIGINAL_KEY_ITERATIONS)
    prefix, _ = hasher.split_encoded(enc)
    return prefix


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
