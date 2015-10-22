from django.db import models
from django.conf import settings
import gnupg
import hashlib

from reports.models import RecordFormItem

class EvalRow(models.Model):
    # TODO: delete, view, export?
    EDIT = "e"
    CREATE = "c"
    SUBMIT = "s"
    VIEW = "v"

    ACTIONS = (
        (EDIT, 'Edit'),
        (CREATE, 'Create'),
        (SUBMIT, 'Submit'),
        (VIEW, 'View')
    )

    identifier = models.CharField(blank=False, max_length=500)
    action = models.CharField(max_length=2,
                              choices=ACTIONS,
                              blank=False)
    row = models.BinaryField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    #TODO: use report instead
    def set_identifier(self, user):
        self.identifier = hashlib.sha256(str(user.id).encode()).hexdigest()

    def encrypt_row(self, row, key = settings.CALLISTO_EVAL_PUBLIC_KEY):
        gpg = gnupg.GPG()
        imported_keys = gpg.import_keys(key)
        encrypted = gpg.encrypt(row, imported_keys.fingerprints[0], armor=True, always_trust=True)
        self.row = encrypted.data

class EvalField(models.Model):
    #If an associated EvalField exists for a record form item, we record the contents
    #If not, we just save whether the question was answered or not
    question = models.OneToOneField(RecordFormItem, primary_key=True)

