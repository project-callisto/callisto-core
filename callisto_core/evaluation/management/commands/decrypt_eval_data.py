import json
import os
import logging

import gnupg
import six

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured

from ...models import EvalRow

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'decrypts eval data. can only be run in local environments (import data from prod)'

    def handle(self, *args, **options):
        if not settings.CALLISTO_EVAL_PRIVATE_KEY:
            raise ImproperlyConfigured('CALLISTO_EVAL_PRIVATE_KEY not present')
        decrypted_eval_data = []
        for row in EvalRow.objects.all():
            decrypted_row = {'pk': row.pk,
                             'user': row.user_identifier,
                             'record': row.record_identifier,
                             'action': row.action,
                             'timestamp': row.timestamp.timestamp()}
            gpg = gnupg.GPG()
            gpg.import_keys(settings.CALLISTO_EVAL_PRIVATE_KEY)
            decrypted_eval_row = six.text_type(gpg.decrypt(six.binary_type(row.row)))
            if decrypted_eval_row:
                decrypted_row.update(json.loads(decrypted_eval_row))
            decrypted_eval_data.append(decrypted_row)
        with open('eval_data.json', 'w') as data_file:
            json.dump(decrypted_eval_data, data_file)
        logger.info("Decrypted eval data written to eval_data.json")
