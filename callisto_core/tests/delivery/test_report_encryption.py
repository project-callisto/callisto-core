import json
from unittest import skip

import gnupg

from django.test import TestCase, override_settings

from callisto_core.delivery.models import Report
from callisto_core.tests.evaluation import test_keypair
from callisto_core.tests.test_base import ReportFlowHelper as ReportFlowTestCase


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class ReportEncryptionTest(ReportFlowTestCase):
    def test_not_authorized_without_owner(self):
        self.report = Report.objects.create()
        response = self.client_post_report_pdf_view(skip_assertions=True)
        self.assertEqual(response.status_code, 403)

    def test_can_decrypt_without_setup(self):
        self.report = Report.objects.create(owner=self.user)
        self.client_post_report_pdf_view()


@skip("disabled for 2019 summer maintenance - record creation is no longer supported")
class ReportGPGEncryptionTest(TestCase):
    @override_settings(CALLISTO_EVAL_PUBLIC_KEY=test_keypair.public_test_key)
    def test_gpg_decryption(self):
        report = Report()
        report._store_for_callisto_decryption({"rawr": "cats"})

        gpg = gnupg.GPG()
        gpg.import_keys(test_keypair.private_test_key)
        gpg_data = gpg.decrypt(report.encrypted_eval)
        data = json.loads(gpg_data.data)

        self.assertEqual(data, {"rawr": "cats"})
