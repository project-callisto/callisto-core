from callisto.delivery.wizard import EncryptedFormBaseWizard
from django.http import HttpResponse


class EncryptedFormWizard(EncryptedFormBaseWizard):

    def wizard_complete(self, report, **kwargs):
        return HttpResponse(report.id)
