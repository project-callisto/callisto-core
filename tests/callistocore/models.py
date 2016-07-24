import hashlib

import nacl.secret
import nacl.utils

from django.conf import settings
from django.utils.crypto import get_random_string, pbkdf2


def _encrypt_report(salt, key, report_text):
    """Encrypts a report using the given secret key & salt. The secret key is stretched to 32 bytes using Django's
    PBKDF2+SHA256 implementation. The encryption uses PyNacl & Salsa20 stream cipher.

    Args:
      salt (str): cryptographic salt
      key (str): secret key
      report_text (str): full report as a string

    Returns:
      bytes: the encrypted bytes of the report

    """
    stretched_key = pbkdf2(key, salt, settings.KEY_ITERATIONS, digest=hashlib.sha256)
    box = nacl.secret.SecretBox(stretched_key)
    message = report_text.encode('utf-8')
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    return box.encrypt(message, nonce)


def _decrypt_report(salt, key, encrypted):
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
    stretched_key = pbkdf2(key, salt, settings.KEY_ITERATIONS, digest=hashlib.sha256)
    box = nacl.secret.SecretBox(stretched_key)
    decrypted = box.decrypt(bytes(encrypted))  # need to force to bytes bc BinaryField can return as memoryview
    return decrypted.decode('utf-8')


def _pepper(encrypted_report):
    """Uses a secret value stored on the server to encrypt an already encrypted report, to add protection if the database
    is breached but the server is not. Requires settings.PEPPER to be set to a 32 byte value. In production, this value
    should be set via environment parameter. Uses PyNacl's Salsa20 stream cipher.

    Args:
      encrypted_report (bytes): the encrypted report

    Returns:
      bytes: a further encrypted report

    """
    pepper = settings.PEPPER
    box = nacl.secret.SecretBox(pepper)
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    return box.encrypt(encrypted_report, nonce)


def _unpepper(peppered_report):
    """Decrypts a report that has been peppered with the _pepper method. Requires settings.PEPPER to be set to a 32
    byte value. In production, this value should be set via environment parameter.

    Args:
      peppered_report(bytes): a report that has been encrypted using a secret key then encrypted using the pepper

    Returns:
      bytes: the report, still encrypted with the secret key

    Raises:
      CryptoError: If the pepper fails to decrypt the record.
    """
    pepper = settings.PEPPER
    box = nacl.secret.SecretBox(pepper)
    decrypted = box.decrypt(bytes(peppered_report))  # need to force to bytes bc BinaryField can return as memoryview
    return decrypted


class LegacyReportData(object):
    """The full text of a reported incident."""
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
        self.encrypted = _encrypt_report(salt=self.salt, key=key, report_text=report_text)


class LegacyMatchReportData(object):
    """A report that indicates the user wants to submit if a match is found. A single report can have multiple
    MatchReports--one per perpetrator.
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
        self.encrypted = _pepper(_encrypt_report(salt=self.salt, key=key, report_text=report_text))
