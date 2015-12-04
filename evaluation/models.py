from django.db import models
from django.conf import settings
import gnupg
import hashlib
from django.core.exceptions import ObjectDoesNotExist

from reports.models import RecordFormItem, MultipleChoice

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

    @staticmethod
    def extract_answers(answered_questions):
        eval_location = {}
        for serialized_question in answered_questions:
            #TODO: handle formset
            if serialized_question['type'] and serialized_question['type'] != 'FormSet':
                try:
                    question = RecordFormItem.objects.get(id=serialized_question['id'])
                    try:
                        label = question.evalfield.label
                        eval_location[label] = serialized_question['answer']
                        if isinstance(question, MultipleChoice):
                                eval_location[label + "_choices"] = question.serialize_choices()
                                if serialized_question['extra']:
                                    eval_location[label + "_extra"] = serialized_question['extra']['answer']
                    except ObjectDoesNotExist:
                            pass #TODO: record whether an answer was entered or not
                except:
                    pass
        return eval_location

class EvalField(models.Model):
    #If an associated EvalField exists for a record form item, we record the contents
    #If not, we (eventually) just save whether the question was answered or not
    question = models.OneToOneField(RecordFormItem, primary_key=True)
    label = models.CharField(blank=False, null=False, max_length=500, unique=True)


