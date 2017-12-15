import json

import gnupg

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from callisto_core.delivery.models import Report
from callisto_core.evaluation.models import EvalRow
from callisto_core.tests.evaluation import test_keypair

User = get_user_model()


class TestModelData(TestCase):

    def test_eval_row_field_generation(self):
        user = User.objects.create()
        record = Report.objects.create(owner=user)
        evalrow = EvalRow.store_eval_row(
            action='TESTING',
            record=record,
            decrypted_record={},
        )
        self.assertTrue(evalrow.action)
        self.assertTrue(evalrow.user)
        self.assertTrue(evalrow.record)
        self.assertTrue(evalrow.record_encrypted)
        self.assertTrue(evalrow.timestamp)

    def test_null_user(self):
        record = Report.objects.create()
        evalrow = EvalRow.store_eval_row(
            action='TESTING',
            record=record,
            decrypted_record={},
        )
        self.assertTrue(evalrow.action)
        self.assertTrue(evalrow.record)
        self.assertTrue(evalrow.record_encrypted)
        self.assertTrue(evalrow.timestamp)

    def test_null_record(self):
        evalrow = EvalRow.store_eval_row(
            action='TESTING',
            record=None,
            decrypted_record={},
        )
        self.assertTrue(evalrow.action)
        self.assertTrue(evalrow.timestamp)

    def test_bad_decrypted_record_format(self):
        user = User.objects.create()
        record = Report.objects.create(owner=user)
        evalrow = EvalRow.store_eval_row(
            action='TESTING',
            record=record,
            decrypted_record=9000,
        )
        self.assertTrue(evalrow.action)
        self.assertTrue(evalrow.user)
        self.assertTrue(evalrow.record)
        self.assertTrue(evalrow.timestamp)

    def test_content_encrypted(self):
        user = User.objects.create()
        record = Report.objects.create(owner=user)
        evalrow = EvalRow.store_eval_row(
            action='TESTING',
            record=record,
            decrypted_record={},
        )
        self.assertNotEqual(evalrow.user, user.id)
        self.assertNotEqual(evalrow.record, record.id)
        self.assertNotEqual(evalrow.record_encrypted, {})

    def test_can_identify_duplicate_data(self):
        user = User.objects.create()
        record_1 = Report.objects.create(owner=user)
        record_2 = Report.objects.create(owner=user)
        evalrow_1 = EvalRow.store_eval_row(
            action='TESTING',
            record=record_1,
            decrypted_record={},
        )
        evalrow_2 = EvalRow.store_eval_row(
            action='TESTING',
            record=record_2,
            decrypted_record={},
        )
        self.assertNotEqual(evalrow_1.user, user.id)
        self.assertEqual(evalrow_1.user, evalrow_2.user)

    @override_settings(CALLISTO_EVAL_PUBLIC_KEY=test_keypair.public_test_key)
    def test_gpg_decryption(self):
        user = User.objects.create()
        record = Report.objects.create(owner=user)
        evalrow = EvalRow.store_eval_row(
            action='TESTING',
            record=record,
            decrypted_record={'rawr': 'cats'},
        )

        gpg = gnupg.GPG()
        gpg.import_keys(test_keypair.private_test_key)
        gpg_data = gpg.decrypt(evalrow.record_encrypted)
        data = json.loads(gpg_data.data)

        self.assertEqual(data, {'rawr': 'cats'})
