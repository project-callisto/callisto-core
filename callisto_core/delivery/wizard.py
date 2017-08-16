from wizard_builder.views import WizardView
from wizard_builder.view_helpers import StorageHelper, StepsHelper

from django.core.urlresolvers import reverse

from .views import ReportAccessView, SecretKeyStorageHelper
from . import security, hashers


class ReportStepsHelper(StepsHelper):

    def url(self, step):
        return reverse(
            self.view.request.resolver_match.view_name,
            kwargs={
                'step': step,
                'uuid': self.view.report.uuid,
            },
        )


class EncryptedStorageHelper(
    SecretKeyStorageHelper,
    StorageHelper,
):

    @property
    def report(self):
        return self.view.report

    def data_from_key(self, form_key):
        return self.report.decrypted_report(self.secret_key).get(form_key, {})

    def update(self):
        self.report.encrypt_report(
            self.form_data,
            self.secret_key,
        )


class EncryptedWizardView(
    ReportAccessView,
    WizardView
):
    template_name = WizardView.template_name
    storage_helper = EncryptedStorageHelper
    steps_helper = ReportStepsHelper
