import hashlib

import nacl.secret
import nacl.utils
from callisto_core.delivery import security

from django.conf import settings
from django.utils.crypto import get_random_string, pbkdf2


def _legacy_encrypt_report(salt, key, report_text):
    """Encrypts a report using the given secret key & salt. The secret key is stretched to 32 bytes using Django's
    PBKDF2+SHA256 implementation. The encryption uses PyNacl & Salsa20 stream cipher.

    Args:
      salt (str): cryptographic salt
      key (str): secret key
      report_text (str): full report as a string

    Returns:
      bytes: the encrypted bytes of the report

    """
    stretched_key = pbkdf2(key, salt, settings.ORIGINAL_KEY_ITERATIONS, digest=hashlib.sha256)
    box = nacl.secret.SecretBox(stretched_key)
    message = report_text.encode('utf-8')
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    return box.encrypt(message, nonce)


def _legacy_decrypt_report(salt, key, encrypted):
    """Decrypts an encrypted report.

    Args:
      salt (str): cryptographic salt
      key (str): secret key
      encrypted (bytes): full report encrypted

    Returns:
      str: the decrypted report as a string

    Raises:
      CryptoError: If the key and salt fail to decrypt the record.

    """
    stretched_key = pbkdf2(key, salt, settings.ORIGINAL_KEY_ITERATIONS, digest=hashlib.sha256)
    box = nacl.secret.SecretBox(stretched_key)
    decrypted = box.decrypt(bytes(encrypted))  # need to force to bytes bc BinaryField can return as memoryview
    return decrypted.decode('utf-8')


class LegacyReportData(object):
    """The full text of a reported incident.

    Uses the old encryption scheme before support for new hashers & increased iterations, for testing that old records
    can still be decrypted.
    """
    encrypted = None
    salt = None

    def encrypt_report(self, report_text, key):
        """Encrypts and attaches report text. Generates a random salt and stores it on the Report object.

        Args:
          report_text (str): the full text of the report
          key (str): the secret key
          edit (obj): the object to edit
          autosave (bool): whether or not this encryption is part of an automatic save

        """
        if not self.salt:
            self.salt = get_random_string()
        self.encrypted = _legacy_encrypt_report(salt=self.salt, key=key, report_text=report_text)


class LegacyMatchReportData(object):
    """A report that indicates the user wants to submit if a match is found. A single report can have multiple
    MatchReports--one per perpetrator.

    Uses the old encryption scheme before support for new hashers & increased iterations, for testing that old records
    can still be decrypted.
    """
    encrypted = None
    salt = None

    def encrypt_match_report(self, report_text, key):
        """Encrypts and attaches report text. Generates a random salt and stores it on the MatchReport object.

        Args:
          report_text (str): the full text of the report
          key (str): the secret key

        """
        self.salt = get_random_string()
        self.encrypted = security.pepper(_legacy_encrypt_report(salt=self.salt, key=key, report_text=report_text))
