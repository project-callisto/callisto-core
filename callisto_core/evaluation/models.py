import hashlib
import json
import logging

import gnupg

from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


def hash_input(inp):
    return hashlib.sha256(str(inp).encode()).hexdigest()


class EvalRow(models.Model):
    """Provides an auditing trail for various records"""

    ACTIONS = (
        ('CREATE', 'CREATE'),
        ('EDIT', 'Edit'),
        ('VIEW', 'VIEW'),
        ('AUTOSAVE', 'AUTOSAVE'),
        ('WITHDRAW', 'WITHDRAW'),
        ('DELETE', 'DELETE'),
    )

    user_identifier = models.TextField(null=True)
    report_identifier = models.TextField(null=True)
    action = models.TextField(null=True)
    record_encrypted = models.BinaryField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    @classmethod
    def store_eval_row(
        self,
        action: str,
        report: 'Report(Model)',
        decrypted_report: dict,
    ):
        try:
            self.action = action
            self._set_identifiers(report)
            self._add_report_data(decrypted_report)
            self.save()
        except BaseException as e:
            # catch and log errors, but ignore them in the user flow
            logger.error(e)

    def _set_identifiers(self, report):
        self.user_identifier = hash_input(report.owner.id)
        self.record_identifier = hash_input(report.id)

    def _add_report_data(self, decrypted_report):
        extracted_answers = self._extract_answers(decrypted_report)
        encrypted_answers = self._encrypt_extracted_answers(extracted_answers)
        self.record_encrypted = encrypted_answers

    def _encrypt_extracted_answers(self, extracted_answers):
        extracted_answers_string = json.dumps(extracted_answers)
        gpg = gnupg.GPG()
        imported_keys = gpg.import_keys(settings.CALLISTO_EVAL_PUBLIC_KEY)
        encrypted = gpg.encrypt(
            extracted_answers_string,
            imported_keys.fingerprints[0],
            armor=True,
            always_trust=True)
        return encrypted.data

    def _extract_answers(self, answered_questions_dict):
        return answered_questions_dict
