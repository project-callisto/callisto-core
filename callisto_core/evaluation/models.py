import copy
import json
import logging
import traceback

import gnupg

from django.conf import settings
from django.db import models

from callisto_core.delivery.models import Report

logger = logging.getLogger(__name__)


def encrypt_filtered_data(filtered_data):
    filtered_data_string = json.dumps(filtered_data)
    gpg = gnupg.GPG()
    imported_keys = gpg.import_keys(settings.CALLISTO_EVAL_PUBLIC_KEY)
    encrypted = gpg.encrypt(
        filtered_data_string,
        imported_keys.fingerprints[0],
        armor=True,
        always_trust=True)
    return encrypted.data


def filter_record_data(record_data):
    filtered_data = copy.copy(record_data)
    try:
        pages = record_data['wizard_form_serialized']
    except TypeError:
        pages = []
    for page in pages:
        for question in page:
            field_id = 'question_' + str(question['id'])
            if (
                question.get('skip_eval') and
                filtered_data.get('data', {}).get(field_id)
            ):
                filtered_data['data'].pop(field_id)
    return filtered_data


class EvalRow(models.Model):
    """Provides an auditing trail for various records"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True)
    record = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
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
            filtered_data = filter_record_data(decrypted_record)
            encrypted_answers = encrypt_filtered_data(filtered_data)
            self.record_encrypted = encrypted_answers
        except BaseException as e:
            logger.error(traceback.format_exc())
