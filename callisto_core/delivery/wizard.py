import logging

from wizard_builder.view_helpers import StepsHelper, StorageHelper
from wizard_builder.views import WizardView

from django.core.urlresolvers import reverse

from .views import ReportFormAccessView, SecretKeyStorageHelper

logger = logging.getLogger(__name__)


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
    invalid_storage_request_messsage = 'data storage requested with secret key set'

    @property
    def report(self):
        return self.view.report

    def current_data_from_storage(self):
        if self.secret_key:
            return self.report.decrypted_report(self.secret_key)
        else:
            logger.warn(self.invalid_storage_request_messsage)
            return {}

    def add_data_to_storage(self, data):
        self.report.encrypt_report(data, self.secret_key)


class EncryptedWizardView(
    ReportFormAccessView,
    WizardView
):
    template_name = 'callisto_core/delivery/wizard_form.html'
    storage_helper = EncryptedStorageHelper
    steps_helper = ReportStepsHelper
