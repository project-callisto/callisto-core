from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
import gnupg

from reports.models import SingleLineText

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
        key_settings = gpg.gen_key_input(key_type='RSA', key_length=1024, key_usage='ESCA')
        key = gpg.gen_key(key_settings)
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


