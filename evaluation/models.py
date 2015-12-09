from django.db import models
from django.conf import settings
import gnupg
import hashlib
import bugsnag
from django.core.exceptions import ObjectDoesNotExist

from reports.models import RecordFormItem, MultipleChoice

class EvalRow(models.Model):
    EDIT = "e"
    CREATE = "c"
    SUBMIT = "s"
    VIEW = "v"
    MATCH = "m"
    FIRST = "f"
    WITHDRAW = "w"

    #TODO: delete
    ACTIONS = (
        (CREATE, 'Create'),
        (EDIT, 'Edit'),
        (VIEW, 'View'),
        (SUBMIT, 'Submit'),
        (MATCH, 'Match'),
        (WITHDRAW, 'Withdraw'),
        (FIRST, 'First'), #for records that were saved before evaluation was implemented--saved on any decryption action
    )

    user_identifier = models.CharField(blank=False, max_length=500)
    record_identifier = models.CharField(blank=False, max_length=500)
    action = models.CharField(max_length=2,
                              choices=ACTIONS,
                              blank=False)
    row = models.BinaryField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def anonymise_row(self, action, report, decrypted=None):
        self.action = action
        self.set_identifiers(report)
        if decrypted:
            self.encrypt_row(decrypted)

    def set_identifiers(self, report):
        self.user_identifier = hashlib.sha256(str(report.owner.id).encode()).hexdigest()
        self.record_identifier = hashlib.sha256(str(report.id).encode()).hexdigest()

    def encrypt_row(self, row, key = settings.CALLISTO_EVAL_PUBLIC_KEY):
        gpg = gnupg.GPG()
        imported_keys = gpg.import_keys(key)
        encrypted = gpg.encrypt(row, imported_keys.fingerprints[0], armor=True, always_trust=True)
        self.row = encrypted.data

    @staticmethod
    def extract_answers(answered_questions):

        def record_if_answered(question_dict, eval_location):
            id = question_dict['id']
            if 'answer' in question_dict and question_dict['answer'].strip():
                eval_location['answered'].append(id)
            else:
                eval_location['unanswered'].append(id)

        def extract_single_question(question_dict, eval_location):
            try:
                record_if_answered(question_dict, eval_location)
                question = RecordFormItem.objects.get(id=question_dict['id'])
                try:
                    label = question.evalfield.label
                    eval_location[label] = question_dict['answer']
                    if isinstance(question, MultipleChoice):
                        eval_location[label + "_choices"] = question.serialize_choices()
                        if 'extra' in question_dict:
                            eval_location[label + "_extra"] = question_dict['extra']['answer']
                except ObjectDoesNotExist:
                        pass #TODO: record whether an answer was entered or not
            except Exception as e:
                #TODO: real logging
                # always fail evaluation code silently
                bugsnag.notify(e)
                pass

        anonymised_answers = {'answered': [], 'unanswered': []}
        for serialized_question in answered_questions:
            try:
                if 'type' in serialized_question:
                    if serialized_question['type'] == 'FormSet':
                        all_pages = []
                        for page in serialized_question['answers']:
                            page_answers = {'answered': [], 'unanswered': []}
                            for question in page:
                                extract_single_question(question, page_answers)
                            all_pages.append(page_answers)
                        anonymised_answers[serialized_question['prompt'] + "_multiple"] = all_pages
                    else:
                        extract_single_question(serialized_question, anonymised_answers)
            except Exception as e:
                #TODO: real logging
                # always fail evaluation code silently
                bugsnag.notify(e)
                pass
        return anonymised_answers

class EvalField(models.Model):
    #If an associated EvalField exists for a record form item, we record the contents
    #If not, we (eventually) just save whether the question was answered or not
    question = models.OneToOneField(RecordFormItem, primary_key=True)
    label = models.CharField(blank=False, null=False, max_length=500, unique=True)


