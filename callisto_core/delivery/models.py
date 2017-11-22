import json
import logging
import uuid

from nacl.exceptions import CryptoError
from polymorphic.models import PolymorphicModel

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

from . import hashers, security, utils

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
    last_edited = models.DateTimeField(blank=True, null=True)

    # <algorithm>$<iterations>$<salt>$
    encode_prefix = models.TextField(blank=True, null=True)
    salt = models.TextField(null=True)  # used for backwards compatibility

    submitted_to_school = models.DateTimeField(blank=True, null=True)
    contact_phone = models.CharField(blank=True, null=True, max_length=256)
    contact_voicemail = models.TextField(default=True)
    contact_email = models.EmailField(blank=True, null=True, max_length=256)
    contact_notes = models.TextField(default='No Preference')
    contact_name = models.TextField(blank=True, null=True)
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

    def encrypt_report(
        self,
        report_text: str,  # the report questions, as a string of json
        passphrase: str,
    ) -> None:
        """
        Encrypts and attaches report text. Generates a random salt
        and stores it in the Report object's encode prefix.
        """
        stretched_key = self.encryption_setup(passphrase)
        json_report_text = json.dumps(report_text)
        self.encrypted = security.encrypt_text(stretched_key, json_report_text)
        self.save()

    def decrypted_report(
        self,
        passphrase: str,  # aka secret key aka passphrase
    ) -> dict or str:
        """
        Decrypts the report text.
        Uses the salt from the encode prefix stored on the Report object.

        Raises:
          CryptoError: If the key and saved salt fail to decrypt the record.
        """
        _, stretched_key = hashers.make_key(
            self.encode_prefix, passphrase, self.salt)
        report_text = security.decrypt_text(stretched_key, self.encrypted)
        try:
            decrypted_data = json.loads(report_text)
            return self._return_or_transform(decrypted_data, passphrase)
        except json.decoder.JSONDecodeError:
            logger.info('decrypting legacy report')
            return report_text

    def withdraw_from_matching(self):
        """ Deletes all associated MatchReports """
        self.matchreport_set.all().delete()
        self.match_found = False
        self.save()

    def encryption_setup(self, passphrase):
        if self.salt:
            self.salt = None
        hasher = hashers.get_hasher()
        encoded = hasher.encode(passphrase, get_random_string())
        self.encode_prefix, stretched_key = hasher.split_encoded(encoded)
        self.save()
        return stretched_key

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        self.last_edited = timezone.now()
        return super().save(*args, **kwargs)

    def _return_or_transform(
        self,
        data: list or dict,
        key: str,  # aka secret key aka passphrase
    ) -> dict:
        '''
        given a set of data in old list or new dict format, return
        the data in the new dict format.

        and save the new data if it was in the old list format
        '''
        if isinstance(data, list):
            new_data = utils.RecordDataUtil.transform_if_old_format(data)
            self.encrypt_report(new_data, key)
            return new_data
        else:
            return data

    class Meta:
        ordering = ('-added',)


class MatchReport(models.Model):
    """
    A report that indicates the user wants to submit if a match is found.
    A single report can have multiple MatchReports--one per perpetrator.
    """
    report = models.ForeignKey('Report', on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)
    encrypted = models.BinaryField(null=False)

    # <algorithm>$<iterations>$<salt>$
    encode_prefix = models.TextField(blank=True)
    salt = models.TextField(null=True)  # used for backwards compatibility

    def __str__(self):
        return "MatchReport for report(pk={0})".format(self.report.pk)

    @property
    def match_found(self):
        self.report.refresh_from_db()
        return self.report.match_found

    def encrypt_match_report(
        self,
        report_text: str,  # MatchReportContent as a string of json
        identifier: str,  # MatchReport is encrypted with the identifier
    ) -> None:
        """
        Encrypts and attaches report text. Generates a random salt and
        stores it in an encode prefix on the MatchReport object.

        MatchReports are encrypted with the identifier, whereas Reports
        are encrypted with the secret key
        """
        if self.salt:
            self.salt = None
        hasher = hashers.get_hasher()
        salt = get_random_string()

        encoded = hasher.encode(identifier, salt)
        self.encode_prefix, stretched_identifier = hasher.split_encoded(
            encoded)

        self.encrypted = security.pepper(
            security.encrypt_text(stretched_identifier, report_text),
        )
        self.save()

    def get_match(
        self,
        identifier: str,  # MatchReport is encrypted with the identifier
    ) -> str or None:
        """
        Checks if the given identifier triggers a match on this report.
        Returns report text if so.
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
    pass

class SentFullReport(models.Model):
    """Report of a single incident since to the monitoring organization"""
    report = models.ForeignKey(
        Report,
        blank=True,
        null=True,
        on_delete=models.SET_NULL)
    sent = models.DateTimeField(auto_now_add=True)
    to_address = models.TextField(blank=False, null=True)

    def get_report_id(self):
        return f'{self.id}-0'


class SentMatchReport(models.Model):
    """Report of multiple incidents, sent to the monitoring organization"""
    reports = models.ManyToManyField(MatchReport)
    sent = models.DateTimeField(auto_now_add=True)
    to_address = models.TextField(blank=False, null=True)

    def get_report_id(self):
        return f'{self.id}-1'
