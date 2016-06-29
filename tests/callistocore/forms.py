from django.http import HttpResponse

from callisto.delivery.wizard import EncryptedFormBaseWizard


class EncryptedFormWizard(EncryptedFormBaseWizard):

    def wizard_complete(self, report, **kwargs):
        return HttpResponse(report.id)
