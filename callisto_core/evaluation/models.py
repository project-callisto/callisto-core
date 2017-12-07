import hashlib
import json
import logging

import gnupg

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from callisto_core.delivery.models import Report
from wizard_builder.models import FormQuestion, MultipleChoice

logger = logging.getLogger(__name__)


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

    user_identifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True)
    report_identifier = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True)
    action = models.TextField(null=True)
    recort_encrypted = models.BinaryField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def anonymise_record(
        self,
        action,
        report,
        decrypted_text=None,
        match_identifier=None,
        key=settings.CALLISTO_EVAL_PUBLIC_KEY,
    ):
        self.action = action
        self.set_identifiers(report)
        if decrypted_text:
            self.add_report_data(
                decrypted_text,
                match_identifier=match_identifier,
                key=key)

    def set_identifiers(self, report):
        self.user_identifier = hashlib.sha256(
            str(report.owner.id).encode()).hexdigest()
        self.record_identifier = hashlib.sha256(
            str(report.id).encode()).hexdigest()

    def _create_eval_row_text(self, decrypted_text, match_identifier=None):
        row = self._extract_answers(json.loads(decrypted_text))
        if match_identifier:
            # Facebook entries are stored without a unique prefix for backwards
            # compatibility
            identifier_type = match_identifier.split(
                ':')[0] if ':' in match_identifier else 'facebook'
            row['match_identifier_type'] = identifier_type
            row['match_identifier'] = hashlib.sha256(
                str(match_identifier).encode()).hexdigest()
        return row

    def add_report_data(
            self,
            decrypted_text,
            match_identifier=None,
            key=settings.CALLISTO_EVAL_PUBLIC_KEY):
        self._encrypt_eval_row(
            json.dumps(
                self._create_eval_row_text(
                    decrypted_text=decrypted_text,
                    match_identifier=match_identifier)),
            key=key)

    def _encrypt_eval_row(
            self,
            eval_row,
            key=settings.CALLISTO_EVAL_PUBLIC_KEY):
        gpg = gnupg.GPG()
        imported_keys = gpg.import_keys(key)
        encrypted = gpg.encrypt(
            eval_row,
            imported_keys.fingerprints[0],
            armor=True,
            always_trust=True)
        self.row = encrypted.data

    def _extract_answers(self, answered_questions_dict):

        def record_if_answered(question_dict, eval_location):
            id = question_dict['id']
            if 'answer' in question_dict and question_dict['answer'] and str(
                    question_dict['answer']).strip():
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
                        eval_location[
                            label + "_choices"] = question.serialize_choices()
                        if 'extra' in question_dict:
                            eval_location[label +
                                          "_extra"] = question_dict['extra']['answer']
                except ObjectDoesNotExist:
                    pass
            except Exception:
                logger.exception(
                    "could not extract an answer in creating eval row")
                # extract other answers if we can

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
                        anonymised_answers[serialized_question['prompt'] +
                                           "_multiple"] = all_pages
                    else:
                        extract_single_question(
                            serialized_question, anonymised_answers)
            except Exception:
                logger.exception(
                    "could not extract an answer in creating eval row")
                # extract other answers if we can

        return anonymised_answers

    @classmethod
    def store_eval_row(
            cls,
            action,
            report,
            decrypted_text=None,
            match_identifier=None):
        try:
            row = EvalRow()
            row.anonymise_record(
                action=action,
                report=report,
                decrypted_text=decrypted_text,
                match_identifier=match_identifier)
            row.save()
        except Exception:
            logger.exception(
                "couldn't save evaluation row on {}".format(
                    dict(
                        EvalRow.ACTIONS).get(action)))
