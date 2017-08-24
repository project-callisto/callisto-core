import json
import logging
import uuid

from nacl.exceptions import CryptoError
from polymorphic.models import PolymorphicModel

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string

from . import hashers, security

logger = logging.getLogger(__name__)


class Report(models.Model):
    """The full text of a reported incident."""
    uuid = models.UUIDField(default=uuid.uuid4)
    encrypted = models.BinaryField(blank=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True)
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
    contact_email_confirmation = models.BooleanField(default=False)
    match_found = models.BooleanField(default=False)

    def __str__(self):
        return 'Report(uuid={})'.format(self.uuid)

    @property
    def entered_into_matching(self):
        first_match_report = self.matchreport_set.first()
        if first_match_report:
            return first_match_report.added
        else:
            return None

    @property
    def get_submitted_report_id(self):
        """Return the ID of the first time a FullReport was submitted."""
        if self.submitted_to_school:
            sent_report = self.sentfullreport_set.first()
            report_id = sent_report.get_report_id() if sent_report else None
            return report_id
        else:
            return None

    def setup(self, secret_key):
        self.encrypt_report({}, secret_key)

    def encrypt_report(self, report_text, secret_key):
        """Encrypts and attaches report text. Generates a random salt
        and stores it in the Report object's encode prefix.

        Args:
          report_text (str): the full text of the report
          secret_key (str): the secret key
        """
        stretched_key = self.encryption_setup(secret_key)
        json_report_text = json.dumps(report_text)
        self.encrypted = security.encrypt_text(stretched_key, json_report_text)
        self.save()

    def decrypted_report(self, key):
        """
        Decrypts the report text.
        Uses the salt from the encode prefix stored on the Report object.

        Args:
          key (str): the secret key

        Returns:
          str: the decrypted report as a string

        Raises:
          CryptoError: If the key and saved salt fail to decrypt the record.
        """
        _, stretched_key = hashers.make_key(self.encode_prefix, key, self.salt)
        report_text = security.decrypt_text(stretched_key, self.encrypted)
        try:
            return json.loads(report_text)
        except json.decoder.JSONDecodeError:
            logger.info('decrypting legacy report')
            return report_text

    def withdraw_from_matching(self):
        """ Deletes all associated MatchReports """
        self.matchreport_set.all().delete()
        self.match_found = False
        self.save()

    def encryption_setup(self, secret_key):
        if self.salt:
            self.salt = None
        hasher = hashers.get_hasher()
        encoded = hasher.encode(secret_key, get_random_string())
        self.encode_prefix, stretched_key = hasher.split_encoded(encoded)
        self.save()
        return stretched_key

    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    class Meta:
        ordering = ('-added',)


class MatchReport(models.Model):
    """A report that indicates the user wants to submit if a match is found. A single report can have multiple
    MatchReports--one per perpetrator.
    """
    report = models.ForeignKey('Report', on_delete=models.CASCADE)
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

    @property
    def match_found(self):
        self.report.refresh_from_db()
        return self.report.match_found

    def encrypt_match_report(self, report_text, key):
        """Encrypts and attaches report text. Generates a random salt and stores it in an encode prefix on the
        MatchReport object.

        Args:
          report_text (str): the full text of the report
          key (str): the secret key

        """
        if self.salt:
            self.salt = None
        hasher = hashers.get_hasher()
        salt = get_random_string()

        encoded = hasher.encode(key, salt)
        self.encode_prefix, stretched_key = hasher.split_encoded(encoded)

        self.encrypted = security.pepper(
            security.encrypt_text(stretched_key, report_text),
        )
        self.save()

    def get_match(self, identifier):
        """
        Checks if the given identifier triggers a match on this report.
        Returns report text if so.

        Args:
          identifier (str): the identifier provided by the user
            when entering matching.

        Returns:
            str or None: returns the decrypted report as a string
                if the identifier matches, or None otherwise.
        """
        decrypted_report = None

        prefix, stretched_identifier = hashers.make_key(
            self.encode_prefix,
            identifier,
            self.salt,
        )

        try:
            decrypted_report = security.decrypt_text(
                stretched_identifier,
                security.unpepper(self.encrypted),
            )
        except CryptoError:
            pass
        return decrypted_report


class SentReport(PolymorphicModel):
    """Report of one or more incidents, sent to the monitoring organization"""
    # TODO: store link to s3 backup
    # https://github.com/SexualHealthInnovations/callisto-core/issues/14
    sent = models.DateTimeField(auto_now_add=True)
    to_address = models.CharField(blank=False, null=False, max_length=4096)

    def _get_id_for_authority(self, is_match):
        return "{0}-{1}-{2}".format(
            settings.SCHOOL_REPORT_PREFIX, '%05d' %
            self.id, 0 if is_match else 1)


class SentFullReport(SentReport):
    """Report of a single incident since to the monitoring organization"""
    report = models.ForeignKey(
        Report,
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    def get_report_id(self):
        return self._get_id_for_authority(is_match=False)


class SentMatchReport(SentReport):
    """Report of multiple incidents, sent to the monitoring organization"""
    reports = models.ManyToManyField(MatchReport)

    def get_report_id(self):
        return self._get_id_for_authority(is_match=True)
