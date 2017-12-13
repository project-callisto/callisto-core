import json
import logging

import gnupg

from django.conf import settings
from django.db import models

from callisto_core.delivery.models import Report

logger = logging.getLogger(__name__)


def encrypt_extracted_answers(extracted_answers):
    extracted_answers_string = json.dumps(extracted_answers)
    gpg = gnupg.GPG()
    imported_keys = gpg.import_keys(settings.CALLISTO_EVAL_PUBLIC_KEY)
    encrypted = gpg.encrypt(
        extracted_answers_string,
        imported_keys.fingerprints[0],
        armor=True,
        always_trust=True)
    return encrypted.data


def extract_answers(answered_questions_dict):
    return answered_questions_dict


class EvalRow(models.Model):
    """Provides an auditing trail for various records"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True)
    record = models.ForeignKey(
        Report,
        on_delete=models.DO_NOTHING,
        null=True)
    action = models.TextField(null=True)
    record_encrypted = models.BinaryField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    @classmethod
    def store_eval_row(
        cls,
        action: str,
        record: Report,
        decrypted_record: dict,
    ):
        self = cls()
        self.action = action
        self.record = record
        self.user = getattr(record, 'owner', None)
        self._add_record_data(decrypted_record)
        self.save()
        return self

    def _add_record_data(self, decrypted_record):
        try:
            extracted_answers = extract_answers(decrypted_record)
            encrypted_answers = encrypt_extracted_answers(extracted_answers)
            self.record_encrypted = encrypted_answers
        except BaseException as e:
            logger.error(e)
