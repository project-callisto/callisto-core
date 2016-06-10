import hashlib
import json

import bugsnag
import gnupg
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from wizard_builder.models import FormQuestion, MultipleChoice


class EvalRow(models.Model):
    EDIT = "e"
    CREATE = "c"
    SUBMIT = "s"
    VIEW = "v"
    MATCH = "m"
    FIRST = "f"
    WITHDRAW = "w"

    # TODO: delete
    ACTIONS = (
        (CREATE, 'Create'),
        (EDIT, 'Edit'),
        (VIEW, 'View'),
        (SUBMIT, 'Submit'),
        (MATCH, 'Match'),
        (WITHDRAW, 'Withdraw'),
        # For records that were saved before evaluation was implemented--saved
        # on any decryption action
        (FIRST, 'First'),
    )

    user_identifier = models.CharField(blank=False, max_length=500)
    record_identifier = models.CharField(blank=False, max_length=500)
    action = models.CharField(max_length=2,
                              choices=ACTIONS,
                              blank=False)
    row = models.BinaryField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def anonymise_record(self, action, report, decrypted_text=None, key=settings.CALLISTO_EVAL_PUBLIC_KEY):
        self.action = action
        self.set_identifiers(report)
        if decrypted_text:
            self.add_report_data(decrypted_text, key=key)

    def set_identifiers(self, report):
        self.user_identifier = hashlib.sha256(str(report.owner.id).encode()).hexdigest()
        self.record_identifier = hashlib.sha256(str(report.id).encode()).hexdigest()

    def add_report_data(self, decrypted_text, key=settings.CALLISTO_EVAL_PUBLIC_KEY):
        self._encrypt_eval_row(json.dumps(self._extract_answers(json.loads(decrypted_text))), key=key)

    def _encrypt_eval_row(self, eval_row, key=settings.CALLISTO_EVAL_PUBLIC_KEY):
        gpg = gnupg.GPG()
        imported_keys = gpg.import_keys(key)
        encrypted = gpg.encrypt(eval_row, imported_keys.fingerprints[0], armor=True, always_trust=True)
        self.row = encrypted.data

    def _extract_answers(self, answered_questions_dict):

        def record_if_answered(question_dict, eval_location):
            id = question_dict['id']
            if 'answer' in question_dict and question_dict['answer'] and str(question_dict['answer']).strip():
                eval_location['answered'].append(id)
            else:
                eval_location['unanswered'].append(id)

        def extract_single_question(question_dict, eval_location):
            try:
                record_if_answered(question_dict, eval_location)
                question = FormQuestion.objects.get(id=question_dict['id'])
                try:
                    label = question.evaluationfield.label
                    eval_location[label] = question_dict['answer']
                    if isinstance(question, MultipleChoice):
                        eval_location[label + "_choices"] = question.serialize_choices()
                        if 'extra' in question_dict:
                            eval_location[label + "_extra"] = question_dict['extra']['answer']
                except ObjectDoesNotExist:
                    pass
            except Exception as e:
                # TODO: real logging
                bugsnag.notify(e)
                # extract other answers if we can
                pass

        anonymised_answers = {'answered': [], 'unanswered': []}
        for serialized_question in answered_questions_dict:
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
                # TODO: real logging
                bugsnag.notify(e)
                # extract other answers if we can
                pass
        return anonymised_answers


class EvaluationField(models.Model):
    # If an associated EvaluationField exists for a record form item, we record the contents
    # If not, we just save whether the question was answered or not
    question = models.OneToOneField(FormQuestion)
    label = models.CharField(blank=False, null=False, max_length=500)
