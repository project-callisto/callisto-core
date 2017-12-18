import json

import gnupg


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
