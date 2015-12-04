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

        anonymised = EvalRow.extract_answers(json_report)

        expected = {
    "q2": "another answer to a different question",
    "radio": str(selected_id),
    "radio_choices": [{"id": choice_ids[0], "choice_text": "This is choice 0"},
                  {"id": choice_ids[1], "choice_text": "This is choice 1"},
                  {"id": choice_ids[2], "choice_text": "This is choice 2"},
                  {"id": choice_ids[3], "choice_text": "This is choice 3"},
                  {"id": choice_ids[4], "choice_text": "This is choice 4"}],
    }
        self.assertEqual(anonymised, expected)

