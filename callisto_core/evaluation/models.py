import hashlib
import json
import logging

import gnupg

from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


def hash_input(inp):
    return hashlib.sha256(str(inp).encode()).hexdigest()


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

    user_identifier = models.TextField(null=True)
    record_identifier = models.TextField(null=True)
    action = models.TextField(null=True)
    record_encrypted = models.BinaryField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    @classmethod
    def store_eval_row(
        cls,
        action: str,
        record: 'Report(Model)',
        decrypted_record: dict,
    ):
        self = cls()
        self.action = action
        self.record = record
        self.decrypted_record = decrypted_record

        for func in [
            self._set_record_identifier,
            self._set_user_identifier,
            self._add_record_data,
        ]:
            try:
                func()
                self.save()
            except BaseException as e:
                logger.error(e)

        return self

    def _set_record_identifier(self):
        self.record_identifier = hash_input(self.record.id)

    def _set_user_identifier(self):
        self.user_identifier = hash_input(self.record.owner.id)

    def _add_record_data(self):
        extracted_answers = extract_answers(self.decrypted_record)
        encrypted_answers = encrypt_extracted_answers(extracted_answers)
        self.record_encrypted = encrypted_answers
