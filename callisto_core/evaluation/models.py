import logging

from django.conf import settings
from django.db import models

from callisto_core.delivery.models import Report

logger = logging.getLogger(__name__)


class EvalRow(models.Model):
    'stores record tracking data'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True)
    record = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True)
    action = models.TextField(null=True)
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
        self.save()
        return self
