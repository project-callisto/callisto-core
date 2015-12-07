from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
import gnupg
import json

from reports.models import SingleLineText, RecordFormQuestionPage, RadioButton, Choice

from .models import EvalRow, EvalField

User = get_user_model()

class EvalRowTest(TestCase):
    def save_row_for_user(self, user):
        row = EvalRow(action=EvalRow.SUBMIT)
        row.set_identifier(user)
        row.save()
        row.full_clean()
        return row

    def test_can_hash_on_user_id(self):
        user = User.objects.create_user(username="dummy", password="dummy")
        self.save_row_for_user(user)
        self.assertEqual(EvalRow.objects.count(), 1)
        self.assertNotEqual(EvalRow.objects.first().identifier, user.id)

    def test_user_hashes_correctly(self):
        user1 = User.objects.create_user(username="dummy", password="dummy")
        user2 = User.objects.create_user(username="dummy1", password="dummy")
        row1 = self.save_row_for_user(user1)
        row2 = self.save_row_for_user(user2)
        row3 = self.save_row_for_user(user1)
        self.assertEqual(EvalRow.objects.count(), 3)
        self.assertEqual(EvalRow.objects.get(id=row1.pk).identifier, EvalRow.objects.get(id=row3.pk).identifier)
        self.assertNotEqual(EvalRow.objects.get(id=row1.pk).identifier, EvalRow.objects.get(id=row2.pk).identifier)

    def test_can_encrypt_a_row(self):
        user = User.objects.create_user(username="dummy", password="dummy")
        row = EvalRow(action=EvalRow.CREATE)
        row.set_identifier(user)
        test_row = "{'test_field': 'test_answer'}"
        row.encrypt_row(test_row)
        row.save()
        row.full_clean()
        self.assertEqual(EvalRow.objects.count(), 1)
        self.assertIsNotNone(EvalRow.objects.get(id=row.pk).row)
        self.assertNotEqual(EvalRow.objects.get(id=row.pk).row, test_row)

    def test_can_decrypt_a_row(self):
        gpg = gnupg.GPG()
        key = gpg.gen_key(gpg.gen_key_input())
        user = User.objects.create_user(username="dummy", password="dummy")
        row = EvalRow(action=EvalRow.CREATE)
        row.set_identifier(user)
        test_row = "{'test_field': 'test_answer'}"
        row.encrypt_row(test_row, key = gpg.export_keys(str(key.fingerprint)))
        row.save()
        row.full_clean()
        self.assertEqual(str(gpg.decrypt(EvalRow.objects.get(id=row.pk).row)), test_row)

class EvalFieldTest(TestCase):

    def test_question_can_have_eval_field(self):
        rfi = SingleLineText(text="This is a question")
        rfi.save()
        EvalField.objects.create(question=rfi)
        self.assertIsNotNone(EvalField.objects.first().question)
        self.assertIsNotNone(SingleLineText.objects.first().evalfield)
        self.assertEqual(SingleLineText.objects.first().evalfield, EvalField.objects.first())

    def test_question_can_not_have_eval_field(self):
        rfi = SingleLineText(text="This is a question")
        rfi.save()
        self.assertRaises(ObjectDoesNotExist, lambda: SingleLineText.objects.first().evalfield)

class ExtractAnswersTest(TestCase):

    def test_extract_answers(self):
        self.maxDiff = None

        page1 = RecordFormQuestionPage.objects.create()
        page2 = RecordFormQuestionPage.objects.create()
        question1 = SingleLineText.objects.create(text="first question", page=page1)
        question2 = SingleLineText.objects.create(text="2nd question", page=page2)
        EvalField.objects.create(question=question2, label="q2")
        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=page2)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question = radio_button_q)
        EvalField.objects.create(question=radio_button_q, label="radio")


        choice_ids = [choice.pk for choice in radio_button_q.choice_set.all()]
        selected_id = choice_ids[2]

        object_ids = [question1.pk, question2.pk, selected_id, radio_button_q.pk,] + choice_ids

        json_report = json.loads("""[
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
  ]""" % tuple(object_ids))

        expected = {
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

        anonymised = EvalRow.extract_answers(json_report)
        self.assertEqual(anonymised, expected)

    def test_extract_answers_with_extra(self):
        self.maxDiff = None
        page1 = RecordFormQuestionPage.objects.create()

        question1 = RadioButton.objects.create(text="this is a radio button question", page=page1)
        for i in range(5):
            choice = Choice.objects.create(text="This is choice %i" % i, question = question1)
            if i == 0:
                choice.extra_info_placeholder = "extra box for choice %i" % i
                choice.save()
        EvalField.objects.create(question=question1, label="q1")

        question2 = RadioButton.objects.create(text="this is another radio button question", page=page1)
        for i in range(5):
            choice = Choice.objects.create(text="This is choice %i" % i, question = question2)
            if i % 2 == 1:
                choice.extra_info_placeholder = "extra box for choice %i" % i
                choice.save()
        EvalField.objects.create(question=question2, label="q2")

        question3 = RadioButton.objects.create(text="this is a radio button question too", page=page1)
        for i in range(5):
            choice = Choice.objects.create(text="This is choice %i" % i, question = question3)
            if i == 0:
                choice.extra_info_placeholder = "extra box for choice %i" % i
                choice.save()
        EvalField.objects.create(question=question3, label="q3")

        q1_choice_ids = [choice.pk for choice in question1.choice_set.all()]
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

        q2_choice_ids = [choice.pk for choice in question2.choice_set.all()]
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

        q3_choice_ids = [choice.pk for choice in question3.choice_set.all()]
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
        anonymised = EvalRow.extract_answers(json_report)
        self.assertEqual(anonymised, expected)

    def test_extract_answers_with_multiple(self):
        self.maxDiff = None

        page1 = RecordFormQuestionPage.objects.create()
        single_question = SingleLineText.objects.create(text="single question", page=page1)
        EvalField.objects.create(question=single_question, label="single_q")

        page2 = RecordFormQuestionPage.objects.create(multiple=True, name_for_multiple="form")
        question1 = SingleLineText.objects.create(text="first question", page=page2)
        question2 = SingleLineText.objects.create(text="2nd question", page=page2)
        EvalField.objects.create(question=question2, label="q2")
        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=page2)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question = radio_button_q)
        EvalField.objects.create(question=radio_button_q, label="radio")

        choice_ids = [choice.pk for choice in radio_button_q.choice_set.all()]
        selected_id_1 = choice_ids[1]
        selected_id_2 = choice_ids[4]
        object_ids = [question1.pk, question2.pk, radio_button_q.pk,] + choice_ids

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
  ]"""% tuple(object_ids)

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
        anonymised = EvalRow.extract_answers(json_report)
        self.assertEqual(anonymised, expected)

    def test_tracking_of_answered_questions(self):
        self.maxDiff = None

        page1 = RecordFormQuestionPage.objects.create()
        question1 = SingleLineText.objects.create(text="first question", page=page1)
        question2 = SingleLineText.objects.create(text="2nd question", page=page1)
        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=page1)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question = radio_button_q)

        choice_ids = [choice.pk for choice in radio_button_q.choice_set.all()]
        object_ids = [question1.pk, question2.pk, radio_button_q.pk,] + choice_ids

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

        anonymised = EvalRow.extract_answers(json_report)
        self.assertEqual(anonymised, expected)