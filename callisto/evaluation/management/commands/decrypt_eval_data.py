import json

import environ
import gnupg
from callisto.evaluation.models import EvalRow
from django.conf import settings
from django.core.management.base import BaseCommand

env = environ.Env()


class Command(BaseCommand):
    help='decrypts eval data. can only be run in local environments (import data from prod)'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise RuntimeError("Don't run this in production!!! Import encrypted prod data to your local environment")
        eval_key = env('CALLISTO_EVAL_PRIVATE_KEY')
        decrypted_eval_data = []
        for row in EvalRow.objects.all():
            decrypted_row = {'pk': row.pk,
                             'user': row.user_identifier,
                             'record': row.record_identifier,
                             'action': row.action,
                             'timestamp': row.timestamp.timestamp()}
            gpg = gnupg.GPG()
            gpg.import_keys(eval_key)
            decrypted_eval_row = str(gpg.decrypt(row.row))
            if decrypted_eval_row:
                decrypted_row.update(json.loads(decrypted_eval_row))
            decrypted_eval_data.append(decrypted_row)
        with open('eval_data.json','w') as output:
            json.dump(decrypted_eval_data, output)
        self.stdout.write("Decrypted eval data written to eval_data.json")
