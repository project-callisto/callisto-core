import json

import gnupg

from django.contrib.auth import get_user_model
from django.test import TestCase

from callisto_core.delivery.models import Report
from callisto_core.evaluation.models import EvalRow

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
