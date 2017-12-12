import unittest

from django.test import TestCase
from django.contrib.auth import get_user_model

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
        self.assertTrue(evalrow.user_identifier)
        self.assertTrue(evalrow.record_identifier)
        self.assertTrue(evalrow.record_encrypted)
        self.assertTrue(evalrow.timestamp)

    def test_content_encrypted(self):
        user = User.objects.create()
        record = Report.objects.create(owner=user)
        evalrow = EvalRow.store_eval_row(
            action='TESTING',
            record=record,
            decrypted_record={},
        )
        self.assertNotEqual(evalrow.user_identifier, user.id)
        self.assertNotEqual(evalrow.record_identifier, record.id)
        self.assertNotEqual(evalrow.record_encrypted, {})
