import uuid

import nacl.secret
import nacl.utils
import six
from nacl.exceptions import CryptoError
from polymorphic.models import PolymorphicModel

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

from .hashers import get_hasher, make_key


def _encrypt_report(stretched_key, report_text):
    """Encrypts a report using the given secret key & salt. Requires a stretched key with a length of 32 bytes.
    The encryption uses PyNacl & Salsa20 stream cipher.

    Args:
      salt (str): cryptographic salt
      stretched_key (str): secret key after being stretched
      report_text (str): full report as a string

    Returns:
      bytes: the encrypted bytes of the report

    """
    box = nacl.secret.SecretBox(stretched_key)
    message = report_text.encode('utf-8')
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    return box.encrypt(message, nonce)


def _decrypt_report(stretched_key, encrypted):
    """Decrypts an encrypted report.

    Args:
      salt (str): cryptographic salt
      stretched_key (str): secret key after being stretched
      encrypted (bytes): full report encrypted

    Returns:
      str: the decrypted report as a string

    Raises:
      CryptoError: If the key and salt fail to decrypt the record.

    """
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


class Report(models.Model):
    """The full text of a reported incident."""
    uuid = models.UUIDField(default=uuid.uuid4)
    encrypted = models.BinaryField(blank=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)
    autosaved = models.BooleanField(null=False, default=False)
    last_edited = models.DateTimeField(blank=True, null=True)

    # DEPRECIATED: only kept to decrypt old entries before upgrade
    salt = models.CharField(null=True, max_length=256)

    # accept blank values for now, as old reports won't have them
    # <algorithm>$<iterations>$<salt>$
    encode_prefix = models.CharField(blank=True, max_length=500)

    submitted_to_school = models.DateTimeField(blank=True, null=True)
    contact_phone = models.CharField(blank=True, null=True, max_length=256)
    contact_voicemail = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True, max_length=256)
    contact_notes = models.TextField(blank=True, null=True)
    contact_name = models.TextField(blank=True, null=True)

    @property
    def entered_into_matching(self):
        first_match_report = self.matchreport_set.first()
        if first_match_report:
            return first_match_report.added
        else:
            return None

    match_found = models.BooleanField(default=False)

    class Meta:
        ordering = ('-added',)

    def encrypt_report(self, report_text, key, edit=False, autosave=False):
        """Encrypts and attaches report text. Generates a random salt and stores it in the Report object's encode
        prefix.

        Args:
          report_text (str): the full text of the report
          key (str): the secret key
          edit (obj): the object to edit
          autosave (bool): whether or not this encryption is part of an automatic save

        """
        # start removing salt fields when updating old entries
        if self.salt:
            self.salt = None

        hasher = get_hasher()
        salt = get_random_string()

        if edit:
            self.last_edited = timezone.now()
        self.autosaved = autosave

        encoded = hasher.encode(key, salt)
        self.encode_prefix, stretched_key = hasher.split_encoded(encoded)

        self.encrypted = _encrypt_report(stretched_key=stretched_key, report_text=report_text)
        self.save()

    def decrypted_report(self, key):
        """Decrypts the report text. Uses the salt from the encode prefix stored on the Report object.
        Args:
          key (str): the secret key

        Returns:
          str: the decrypted report as a string

        Raises:
          CryptoError: If the key and saved salt fail to decrypt the record.
        """
        prefix, stretched_key = make_key(self.encode_prefix, key, self.salt)

        return _decrypt_report(stretched_key=stretched_key, encrypted=self.encrypted)

    def withdraw_from_matching(self):
        """ Deletes all associated MatchReports """
        self.matchreport_set.all().delete()
        self.match_found = False

    @property
    def get_submitted_report_id(self):
        """Return the ID of the first time a FullReport was submitted."""
        if self.submitted_to_school:
            sent_report = self.sentfullreport_set.first()
            report_id = sent_report.get_report_id() if sent_report else None
            return report_id
        else:
            return None


@six.python_2_unicode_compatible
class MatchReport(models.Model):
    """A report that indicates the user wants to submit if a match is found. A single report can have multiple
    MatchReports--one per perpetrator.
    """
    report = models.ForeignKey('Report', on_delete=models.CASCADE)
    contact_email = models.EmailField(blank=False, max_length=256)

    identifier = models.CharField(blank=False, null=True, max_length=500)

    added = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(blank=False, default=False)

    encrypted = models.BinaryField(null=False)

    # DEPRECIATED: only kept to decrypt old entries before upgrade
    salt = models.CharField(null=True, max_length=256)

    # <algorithm>$<iterations>$<salt>$
    encode_prefix = models.CharField(blank=True, max_length=500)

    def __str__(self):
        return "Match report for report {0}".format(self.report.pk)

    def encrypt_match_report(self, report_text, key):
        """Encrypts and attaches report text. Generates a random salt and stores it in an encode prefix on the
        MatchReport object.

        Args:
          report_text (str): the full text of the report
          key (str): the secret key

        """
        if self.salt:
            self.salt = None
        hasher = get_hasher()
        salt = get_random_string()

        encoded = hasher.encode(key, salt)
        self.encode_prefix, stretched_key = hasher.split_encoded(encoded)

        self.encrypted = _pepper(_encrypt_report(stretched_key=stretched_key, report_text=report_text))

    def get_match(self, identifier):
        """Checks if the given identifier triggers a match on this report. Returns report text if so.

        Args:
          identifier (str): the identifier provided by the user when entering matching.

        Returns:
            str or None: returns the decrypted report as a string if the identifier matches, or None otherwise.
        """
        decrypted_report = None

        prefix, stretched_identifier = make_key(self.encode_prefix, identifier, self.salt)

        try:
            decrypted_report = _decrypt_report(stretched_key=stretched_identifier,
                                               encrypted=_unpepper(self.encrypted))
        except CryptoError:
            pass
        return decrypted_report


class SentReport(PolymorphicModel):
    """Report of one or more incidents, sent to the monitoring organization"""
    # TODO: store link to s3 backup https://github.com/SexualHealthInnovations/callisto-core/issues/14
    sent = models.DateTimeField(auto_now_add=True)
    to_address = models.CharField(blank=False, null=False, max_length=4096)

    def _get_id_for_authority(self, is_match):
        return "{0}-{1}-{2}".format(settings.SCHOOL_REPORT_PREFIX, '%05d' % self.id, 0 if is_match else 1)


class SentFullReport(SentReport):
    """Report of a single incident since to the monitoring organization"""
    report = models.ForeignKey(Report, blank=True, null=True, on_delete=models.SET_NULL)

    def get_report_id(self):
        return self._get_id_for_authority(is_match=False)


class SentMatchReport(SentReport):
    """Report of multiple incidents, sent to the monitoring organization"""
    reports = models.ManyToManyField(MatchReport)

    def get_report_id(self):
        return self._get_id_for_authority(is_match=True)
