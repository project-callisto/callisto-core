import json

import gnupg
import six
from mock import ANY, call, patch
from wizard_builder.models import (
    Checkbox, Choice, QuestionPage, RadioButton, SingleLineText,
)

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from django.test import TestCase

from callisto.delivery.matching import MatchingApi
from callisto.delivery.models import Report
from callisto.evaluation.models import EvalRow, EvaluationField

from ..callistocore.test_matching import MatchTest
from .test_keypair import private_test_key, public_test_key

User = get_user_model()


def delete_test_key(gpg, identifier):
    private_key_delete = str(gpg.delete_keys(identifier, True))
    if private_key_delete != 'ok':
        raise RuntimeError('delete of test GPG private key failed: ' + private_key_delete)
    public_key_delete = str(gpg.delete_keys(identifier))
    if public_key_delete != 'ok':
        raise RuntimeError('delete of test GPG public key failed: ' + public_key_delete)


class EvalRowTest(TestCase):

    def save_row_for_report(self, report):
        row = EvalRow(action=EvalRow.SUBMIT)
        row.set_identifiers(report)
        row.full_clean()
        row.save()
        return row

    def test_can_hash_on_user_id(self):
        user = User.objects.create_user(username="dummy", password="dummy")
        report = Report.objects.create(owner=user, encrypted=b'first report')
        self.save_row_for_report(report)
        self.assertEqual(EvalRow.objects.count(), 1)
        self.assertNotEqual(EvalRow.objects.first().user_identifier, user.id)
        self.assertNotEqual(EvalRow.objects.first().record_identifier, report.id)

    def test_user_hashes_correctly(self):
        user1 = User.objects.create_user(username="dummy", password="dummy")
        report1 = Report.objects.create(owner=user1, encrypted=b'first report')
        user2 = User.objects.create_user(username="dummy1", password="dummy")
        report2 = Report.objects.create(owner=user2, encrypted=b'second report')
        report3 = Report.objects.create(owner=user1, encrypted=b'third report')
        row1 = self.save_row_for_report(report1)
        row2 = self.save_row_for_report(report2)
        row3 = self.save_row_for_report(report3)
        self.assertEqual(EvalRow.objects.count(), 3)
        self.assertEqual(EvalRow.objects.get(id=row1.pk).user_identifier,
                         EvalRow.objects.get(id=row3.pk).user_identifier)
        self.assertNotEqual(EvalRow.objects.get(id=row1.pk).user_identifier,
                            EvalRow.objects.get(id=row2.pk).user_identifier)

    def test_report_hashes_correctly(self):
        user1 = User.objects.create_user(username="dummy", password="dummy")
        report1 = Report.objects.create(owner=user1, encrypted=b'first report')
        user2 = User.objects.create_user(username="dummy1", password="dummy")
        report2 = Report.objects.create(owner=user2, encrypted=b'second report')
        report3 = Report.objects.create(owner=user1, encrypted=b'third report')
        row1 = self.save_row_for_report(report1)
        row2 = self.save_row_for_report(report2)
        row3 = self.save_row_for_report(report3)
        row3_edit = EvalRow(action=EvalRow.EDIT)
        row3_edit.set_identifiers(report3)
        row3_edit.save()
        row3_edit.full_clean()
        self.assertEqual(EvalRow.objects.count(), 4)
        self.assertNotEqual(EvalRow.objects.get(id=row2.pk).record_identifier,
                            EvalRow.objects.get(id=row3.pk).record_identifier)
        self.assertNotEqual(EvalRow.objects.get(id=row1.pk).record_identifier,
                            EvalRow.objects.get(id=row2.pk).record_identifier)
        self.assertEqual(EvalRow.objects.get(id=row3.pk).record_identifier,
                         EvalRow.objects.get(id=row3_edit.pk).record_identifier)

    def test_can_encrypt_a_row(self):
        user = User.objects.create_user(username="dummy", password="dummy")
        report = Report.objects.create(owner=user, encrypted=b'first report')
        row = EvalRow(action=EvalRow.CREATE)
        row.set_identifiers(report)
        test_row = "{'test_field': 'test_answer'}"
        row._encrypt_eval_row(test_row)
        row.save()
        row.full_clean()
        self.assertEqual(EvalRow.objects.count(), 1)
        self.assertIsNotNone(EvalRow.objects.get(id=row.pk).row)
        self.assertNotEqual(EvalRow.objects.get(id=row.pk).row, test_row)

    def test_can_decrypt_a_row(self):
        gpg = gnupg.GPG()
        test_key = gpg.import_keys(private_test_key)
        self.addCleanup(delete_test_key, gpg, test_key.fingerprints[0])
        user = User.objects.create_user(username="dummy", password="dummy")
        report = Report.objects.create(owner=user, encrypted=b'first report')
        row = EvalRow(action=EvalRow.CREATE)
        row.set_identifiers(report)
        test_row = "{'test_field': 'test_answer'}"
        row._encrypt_eval_row(test_row, key=public_test_key)
        row.save()
        row.full_clean()
        self.assertEqual(six.text_type(gpg.decrypt(six.binary_type(EvalRow.objects.get(id=row.pk).row))), test_row)

    def test_make_eval_row(self):
        user = User.objects.create_user(username="dummy", password="dummy")
        report = Report.objects.create(owner=user, encrypted=b'first report')
        EvalRow.store_eval_row(EvalRow.CREATE, report=report)
        self.assertEqual(EvalRow.objects.count(), 1)


class EvalFieldTest(TestCase):

    def test_question_can_have_eval_field(self):
        page = QuestionPage.objects.create()
        rfi = SingleLineText(text="This is a question", page=page)
        rfi.save()
        EvaluationField.objects.create(question=rfi)
        self.assertIsNotNone(EvaluationField.objects.first().question)
        self.assertIsNotNone(SingleLineText.objects.first().evaluationfield)
        self.assertEqual(SingleLineText.objects.first().evaluationfield, EvaluationField.objects.first())

    def test_question_can_not_have_eval_field(self):
        page = QuestionPage.objects.create()
        rfi = SingleLineText(text="This is a question", page=page)
        rfi.save()
        self.assertRaises(ObjectDoesNotExist, lambda: SingleLineText.objects.first().evaluationfield)

    def test_evalfield_label_is_non_unique(self):
        page = QuestionPage.objects.create()
        q1 = SingleLineText(text="This is a question", page=page)
        q1.save()
        EvaluationField.objects.create(question=q1, label="question")
        q2 = SingleLineText(text="This is also a question", page=page)
        q2.save()
        EvaluationField.objects.create(question=q2, label="question")
        self.assertEqual(EvaluationField.objects.all().count(), 2)


class ExtractAnswersTest(TestCase):

    def set_up_simple_report_scenario(self):
        page1 = QuestionPage.objects.create()
        page2 = QuestionPage.objects.create()
        question1 = SingleLineText.objects.create(text="first question", page=page1)
        question2 = SingleLineText.objects.create(text="2nd question", page=page2)
        EvaluationField.objects.create(question=question2, label="q2")
        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=page2)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question=radio_button_q)
        EvaluationField.objects.create(question=radio_button_q, label="radio")

        choice_ids = [ch.pk for ch in radio_button_q.choice_set.all()]
        selected_id = choice_ids[2]

        object_ids = [question1.pk, question2.pk, selected_id, radio_button_q.pk, ] + choice_ids

        self.json_report = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    },
    { "answer": "%i",
      "id": %i,
      "section": 1,
      "question_text": "this is a radio button question",
            "choices": [{"id": %i, "choice_text": "This is choice 0"},
                  {"id": %i, "choice_text": "This is choice 1"},
                  {"id": %i, "choice_text": "This is choice 2"},
                  {"id": %i, "choice_text": "This is choice 3"},
                  {"id": %i, "choice_text": "This is choice 4"}],
      "type": "RadioButton"
    }
  ]""" % tuple(object_ids)

        self.expected = {
            "q2": "another answer to a different question",
            "radio": str(selected_id),
            "radio_choices": [{"id": choice_ids[0], "choice_text": "This is choice 0"},
                              {"id": choice_ids[1], "choice_text": "This is choice 1"},
                              {"id": choice_ids[2], "choice_text": "This is choice 2"},
                              {"id": choice_ids[3], "choice_text": "This is choice 3"},
                              {"id": choice_ids[4], "choice_text": "This is choice 4"}],
            "answered": [question1.pk, question2.pk, radio_button_q.pk],
            "unanswered": []
        }

    def test_extract_answers(self):
        self.maxDiff = None
        self.set_up_simple_report_scenario()
        anonymised = EvalRow()._extract_answers(json.loads(self.json_report))
        self.assertEqual(anonymised, self.expected)

    def test_match_id_gets_appended(self):
        self.set_up_simple_report_scenario()
        anonymised1 = EvalRow()._create_eval_row_text(self.json_report, match_identifier='dummy1')
        anonymised2 = EvalRow()._create_eval_row_text(self.json_report, match_identifier='dummy1')
        anonymised3 = EvalRow()._create_eval_row_text(self.json_report, match_identifier='dummy2')
        self.assertNotEqual(anonymised1['match_identifier'], 'dummy1')
        self.assertEqual(anonymised1['match_identifier'], anonymised2['match_identifier'])
        self.assertNotEqual(anonymised1['match_identifier'], anonymised3['match_identifier'])

    def test_extract_answers_with_extra(self):
        self.maxDiff = None
        page1 = QuestionPage.objects.create()

        question1 = RadioButton.objects.create(text="this is a radio button question", page=page1)
        for i in range(5):
            choice = Choice.objects.create(text="This is choice %i" % i, question=question1)
            if i == 0:
                choice.extra_info_placeholder = "extra box for choice %i" % i
                choice.save()
        EvaluationField.objects.create(question=question1, label="q1")

        question2 = RadioButton.objects.create(text="this is another radio button question", page=page1)
        for i in range(5):
            choice = Choice.objects.create(text="This is choice %i" % i, question=question2)
            if i % 2 == 1:
                choice.extra_info_placeholder = "extra box for choice %i" % i
                choice.save()
        EvaluationField.objects.create(question=question2, label="q2")

        question3 = RadioButton.objects.create(text="this is a radio button question too", page=page1)
        for i in range(5):
            choice = Choice.objects.create(text="This is choice %i" % i, question=question3)
            if i == 0:
                choice.extra_info_placeholder = "extra box for choice %i" % i
                choice.save()
        EvaluationField.objects.create(question=question3, label="q3")

        q1_choice_ids = [ch.pk for ch in question1.choice_set.all()]
        q1_selected_id = q1_choice_ids[1]
        first_q_object_ids = [q1_selected_id, question1.pk] + q1_choice_ids
        first_q_output = """{
          "answer": "%i",
          "id": %i,
          "question_text": "this is a radio button question",
                "choices": [{"id": %i, "choice_text": "This is choice 0"},
                      {"id": %i, "choice_text": "This is choice 1"},
                      {"id": %i, "choice_text": "This is choice 2"},
                      {"id": %i, "choice_text": "This is choice 3"},
                      {"id": %i, "choice_text": "This is choice 4"}],
          "type": "RadioButton",
          "section": 1
         }""" % tuple(first_q_object_ids)

        q2_choice_ids = [ch.pk for ch in question2.choice_set.all()]
        q2_selected_id = q2_choice_ids[3]
        second_q_object_ids = [q2_selected_id, question2.pk] + q2_choice_ids
        second_q_output = """{
          "answer": "%i",
          "id": %i,
          "question_text": "this is another radio button question",
                "choices": [{"id": %i, "choice_text": "This is choice 0"},
                      {"id": %i, "choice_text": "This is choice 1"},
                      {"id": %i, "choice_text": "This is choice 2"},
                      {"id": %i, "choice_text": "This is choice 3"},
                      {"id": %i, "choice_text": "This is choice 4"}],
          "type": "RadioButton",
          "section": 1,
          "extra": {
                    "extra_text": "extra box for choice 3",
                    "answer": "this should be in the report"
                    }
         }""" % tuple(second_q_object_ids)

        q3_choice_ids = [ch.pk for ch in question3.choice_set.all()]
        q3_selected_id = q3_choice_ids[0]
        third_q_object_ids = [q3_selected_id, question3.pk] + q3_choice_ids
        third_q_output = """{
          "answer": "%i",
          "id": %i,
          "section": 1,
          "question_text": "this is a radio button question too",
                "choices": [{"id": %i, "choice_text": "This is choice 0"},
                      {"id": %i, "choice_text": "This is choice 1"},
                      {"id": %i, "choice_text": "This is choice 2"},
                      {"id": %i, "choice_text": "This is choice 3"},
                      {"id": %i, "choice_text": "This is choice 4"}],
          "type": "RadioButton",
          "extra": {
                    "extra_text": "extra box for choice 0",
                    "answer": ""
                    }
         }""" % tuple(third_q_object_ids)

        json_report = json.loads("[%s, %s, %s]" % (first_q_output, second_q_output, third_q_output))

        expected = {
            "q1": str(q1_selected_id),
            "q1_choices": [{"id": q1_choice_ids[0], "choice_text": "This is choice 0"},
                           {"id": q1_choice_ids[1], "choice_text": "This is choice 1"},
                           {"id": q1_choice_ids[2], "choice_text": "This is choice 2"},
                           {"id": q1_choice_ids[3], "choice_text": "This is choice 3"},
                           {"id": q1_choice_ids[4], "choice_text": "This is choice 4"}],
            "q2": str(q2_selected_id),
            "q2_choices": [{"id": q2_choice_ids[0], "choice_text": "This is choice 0"},
                           {"id": q2_choice_ids[1], "choice_text": "This is choice 1"},
                           {"id": q2_choice_ids[2], "choice_text": "This is choice 2"},
                           {"id": q2_choice_ids[3], "choice_text": "This is choice 3"},
                           {"id": q2_choice_ids[4], "choice_text": "This is choice 4"}],
            "q2_extra": "this should be in the report",
            "q3": str(q3_selected_id),
            "q3_choices": [{"id": q3_choice_ids[0], "choice_text": "This is choice 0"},
                           {"id": q3_choice_ids[1], "choice_text": "This is choice 1"},
                           {"id": q3_choice_ids[2], "choice_text": "This is choice 2"},
                           {"id": q3_choice_ids[3], "choice_text": "This is choice 3"},
                           {"id": q3_choice_ids[4], "choice_text": "This is choice 4"}],
            "q3_extra": "",
            "answered": [question1.pk, question2.pk, question3.pk],
            "unanswered": []
        }
        anonymised = EvalRow()._extract_answers(json_report)
        self.assertEqual(anonymised, expected)

    def test_extract_answers_with_multiple(self):
        self.maxDiff = None

        page1 = QuestionPage.objects.create()
        single_question = SingleLineText.objects.create(text="single question", page=page1)
        EvaluationField.objects.create(question=single_question, label="single_q")

        page2 = QuestionPage.objects.create(multiple=True, name_for_multiple="form")
        question1 = SingleLineText.objects.create(text="first question", page=page2)
        question2 = SingleLineText.objects.create(text="2nd question", page=page2)
        EvaluationField.objects.create(question=question2, label="q2")
        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=page2)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question=radio_button_q)
        EvaluationField.objects.create(question=radio_button_q, label="radio")

        choice_ids = [ch.pk for ch in radio_button_q.choice_set.all()]
        selected_id_1 = choice_ids[1]
        selected_id_2 = choice_ids[4]
        object_ids = [question1.pk, question2.pk, radio_button_q.pk, ] + choice_ids

        answer_set_template = """[
    { "answer": "test answer <PREFIX> answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "<PREFIX> answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    },
    { "answer": "<SELECTED>",
      "id": %i,
      "section": 1,
      "question_text": "this is a radio button question",
            "choices": [{"id": %i, "choice_text": "This is choice 0"},
                  {"id": %i, "choice_text": "This is choice 1"},
                  {"id": %i, "choice_text": "This is choice 2"},
                  {"id": %i, "choice_text": "This is choice 3"},
                  {"id": %i, "choice_text": "This is choice 4"}],
      "type": "RadioButton"
    }
  ]""" % tuple(object_ids)

        answer_set_one = answer_set_template.replace("<PREFIX>", "first").replace("<SELECTED>", str(selected_id_1))
        answer_set_two = answer_set_template.replace("<PREFIX>", "second").replace("<SELECTED>", str(selected_id_2))

        json_report = json.loads("""
      [ { "answer": "single answer",
          "id": %i,
          "section": 1,
          "question_text": "single question",
          "type": "SingleLineText"
        },
        { "answers" : [ %s, %s],
            "page_id" : %i,
            "prompt" : "form",
            "section" : 1,
            "type" : "FormSet"
        } ]""" % (single_question.pk, answer_set_one, answer_set_two, page2.pk))

        expected = {'single_q': 'single answer',
                    "answered": [single_question.pk],
                    "unanswered": [],
                    'form_multiple':
                    [{
                        "q2": "first answer to a different question",
                        "radio": str(selected_id_1),
                        "radio_choices": [{"id": choice_ids[0], "choice_text": "This is choice 0"},
                                          {"id": choice_ids[1], "choice_text": "This is choice 1"},
                                          {"id": choice_ids[2], "choice_text": "This is choice 2"},
                                          {"id": choice_ids[3], "choice_text": "This is choice 3"},
                                          {"id": choice_ids[4], "choice_text": "This is choice 4"}],
                        "answered": [question1.pk, question2.pk, radio_button_q.pk],
                        "unanswered": []
                    },
                        {
                        "q2": "second answer to a different question",
                        "radio": str(selected_id_2),
                        "radio_choices": [{"id": choice_ids[0], "choice_text": "This is choice 0"},
                                          {"id": choice_ids[1], "choice_text": "This is choice 1"},
                                          {"id": choice_ids[2], "choice_text": "This is choice 2"},
                                          {"id": choice_ids[3], "choice_text": "This is choice 3"},
                                          {"id": choice_ids[4], "choice_text": "This is choice 4"}],
                        "answered": [question1.pk, question2.pk, radio_button_q.pk],
                        "unanswered": []
                    }]}
        anonymised = EvalRow()._extract_answers(json_report)
        self.assertEqual(anonymised, expected)

    def test_tracking_of_answered_questions(self):
        self.maxDiff = None

        page1 = QuestionPage.objects.create()
        question1 = SingleLineText.objects.create(text="first question", page=page1)
        question2 = SingleLineText.objects.create(text="2nd question", page=page1)
        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=page1)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question=radio_button_q)

        choice_ids = [ch.pk for ch in radio_button_q.choice_set.all()]
        object_ids = [question1.pk, question2.pk, radio_button_q.pk, ] + choice_ids

        json_report = json.loads("""[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": " ",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    },
    { "answer": "",
      "id": %i,
      "section": 1,
      "question_text": "this is a radio button question",
            "choices": [{"id": %i, "choice_text": "This is choice 0"},
                  {"id": %i, "choice_text": "This is choice 1"},
                  {"id": %i, "choice_text": "This is choice 2"},
                  {"id": %i, "choice_text": "This is choice 3"},
                  {"id": %i, "choice_text": "This is choice 4"}],
      "type": "RadioButton"
    }
  ]""" % tuple(object_ids))

        expected = {
            "answered": [question1.pk],
            "unanswered": [question2.pk, radio_button_q.pk]
        }

        anonymised = EvalRow()._extract_answers(json_report)
        self.assertEqual(anonymised, expected)

    def test_tracking_of_answered_questions_checkbox(self):
        self.maxDiff = None

        page1 = QuestionPage.objects.create()
        checkbox_q_1 = Checkbox.objects.create(text="this is a checkbox question", page=page1)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question=checkbox_q_1)
        checkbox_q_2 = Checkbox.objects.create(text="this is another checkbox question", page=page1)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question=checkbox_q_2)

        choice_ids_1 = [ch.pk for ch in checkbox_q_1.choice_set.all()]
        choice_ids_2 = [ch.pk for ch in checkbox_q_2.choice_set.all()]
        object_ids = [checkbox_q_1.pk] + choice_ids_1 + \
            [choice_ids_2[1], choice_ids_2[3], checkbox_q_2.pk] + choice_ids_2

        json_report = json.loads("""[
    { "answer": [],
      "id": %i,
      "section": 1,
      "question_text": "this is a checkbox question",
            "choices": [{"id": %i, "choice_text": "This is choice 0"},
                  {"id": %i, "choice_text": "This is choice 1"},
                  {"id": %i, "choice_text": "This is choice 2"},
                  {"id": %i, "choice_text": "This is choice 3"},
                  {"id": %i, "choice_text": "This is choice 4"}],
      "type": "Checkbox"
    },
    { "answer": ["%i", "%i"],
      "id": %i,
      "section": 1,
      "question_text": "this is another checkbox question",
            "choices": [{"id": %i, "choice_text": "This is choice 0"},
                  {"id": %i, "choice_text": "This is choice 1"},
                  {"id": %i, "choice_text": "This is choice 2"},
                  {"id": %i, "choice_text": "This is choice 3"},
                  {"id": %i, "choice_text": "This is choice 4"}],
      "type": "Checkbox"
    }
  ]""" % tuple(object_ids))

        expected = {
            "answered": [checkbox_q_2.pk],
            "unanswered": [checkbox_q_1.pk]
        }

        anonymised = EvalRow()._extract_answers(json_report)
        self.assertEqual(anonymised, expected)

    def test_anonymise_record_end_to_end(self):
        self.maxDiff = None

        self.set_up_simple_report_scenario()

        user = User.objects.create_user(username="dummy", password="dummy")
        report = Report.objects.create(owner=user, encrypted=b'dummy report')

        gpg = gnupg.GPG()
        test_key = gpg.import_keys(private_test_key)
        self.addCleanup(delete_test_key, gpg, test_key.fingerprints[0])

        row = EvalRow()
        row.anonymise_record(action=EvalRow.CREATE, report=report, decrypted_text=self.json_report,
                             key=public_test_key)
        row.save()

        self.assertEqual(json.loads(six.text_type(gpg.decrypt(six.binary_type(EvalRow.objects.get(id=row.pk).row)))),
                         self.expected)


class EvalActionTest(MatchTest):

    def setUp(self):
        super(EvalActionTest, self).setUp()

        self.page1 = QuestionPage.objects.create()
        self.page2 = QuestionPage.objects.create()
        self.question1 = SingleLineText.objects.create(text="first question", page=self.page1)
        self.question2 = SingleLineText.objects.create(text="2nd question", page=self.page2)

        self.client.login(username='dummy', password='dummy')
        self.request = HttpRequest()
        self.request.GET = {}
        self.request.method = 'GET'
        self.request.user = User.objects.get(username='dummy')

        self.report_text = json.dumps({'test_question': 'test answer'})
        self.key = 'a key a key a key'
        self.report = Report(owner=self.user1)
        self.report.encrypt_report(self.report_text, self.key)
        self.report.save()

    @patch('callisto.delivery.views.MatchingApi')
    @patch('callisto.delivery.views.EvalRow.anonymise_record')
    def test_submission_to_matching_creates_eval_row(self, mock_anonymise_record, mock_matching_api):
        response = self.client.post(('/test_reports/match/%s/' % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.key,
                                          'form-0-perp': 'facebook.com/test_url',
                                          'form-TOTAL_FORMS': '1',
                                          'form-INITIAL_FORMS': '1',
                                          'form-MAX_NUM_FORMS': '', })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        mock_anonymise_record.assert_called_with(action=EvalRow.MATCH, report=self.report, match_identifier="test_url",
                                                 decrypted_text=None)

    @patch('callisto.delivery.matching.EvalRow.anonymise_record')
    @patch('callisto.notification.api.NotificationApi.send_match_notification')
    @patch('callisto.notification.api.NotificationApi.send_matching_report_to_authority')
    def test_match_trigger_creates_eval_row(self, mock_send_to_authority, mock_notify, mock_anonymise_record):
        match1 = self.create_match(self.user1, 'dummy')
        match2 = self.create_match(self.user2, 'dummy')
        MatchingApi().run_matching()
        call1 = call(action=EvalRow.MATCH_FOUND, report=match1.report, decrypted_text=None, match_identifier=None)
        call2 = call(action=EvalRow.MATCH_FOUND, report=match2.report, decrypted_text=None, match_identifier=None)
        mock_anonymise_record.assert_has_calls([call1, call2])

    @patch('callisto.delivery.views.EvalRow.anonymise_record')
    @patch('callisto.notification.api.NotificationApi.send_report_to_authority')
    def test_submit_creates_eval_row(self, mock_send_report, mock_anonymise_record):
        response = self.client.post(('/test_reports/submit/%s/' % self.report.pk),
                                    data={'name': 'test submitter',
                                          'email': 'test@example.com',
                                          'phone_number': '555-555-1212',
                                          'email_confirmation': "False",
                                          'key': self.key})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        mock_anonymise_record.assert_called_with(action=EvalRow.SUBMIT, report=self.report, decrypted_text=None,
                                                 match_identifier=None)

    @patch('callisto.delivery.views.EvalRow.anonymise_record')
    @patch('callisto.delivery.views.Report.delete')
    def test_delete_creates_eval_row(self, mock_delete, mock_anonymise_record):
        response = self.client.post(
            '/test_reports/delete/%s/' % self.report.id,
            data={'key': self.key},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('submit_error', response.context)
        mock_anonymise_record.assert_called_with(action=EvalRow.DELETE, report=self.report, decrypted_text=None,
                                                 match_identifier=None)

    @patch('callisto.delivery.views.EvalRow.anonymise_record')
    def test_autosave_creates_eval_row(self, mock_anonymise_record):
        response = self.client.post(
            '/test_reports/new/0/',
            data={'0-key': self.key,
                  '0-key2': self.key,
                  'form_wizard-current_step': 0},
            follow=True
        )
        self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question1.pk: 'test answer',
                  'form_wizard-current_step': 1,
                  'wizard_goto_step': 2},
            follow=True)
        self.client.get("www.google.com")
        # JSON sorting is making this test flap
        mock_anonymise_record.assert_called_with(action=EvalRow.AUTOSAVE, report=Report.objects.first(),
                                                 decrypted_text=ANY, match_identifier=None)
