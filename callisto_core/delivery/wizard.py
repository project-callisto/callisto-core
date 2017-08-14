from wizard_builder.views import StepsHelper, StorageHelper, WizardView
from django.core.urlresolvers import reverse

from django.http.response import JsonResponse

from .models import Report
from .views import ReportAccessView, SecretKeyStorageHelper


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
    def form_data(self):
        return self.decrypt(super().form_data)

    @property
    def post_data(self):
        return self.encrypt(super().post_data)

    def encrypt(self, data):
        return data  # TODO

    def decrypt(self, data):
        return data  # TODO


class EncryptedWizardView(ReportAccessView, WizardView):
    storage_helper = EncryptedStorageHelper
    steps_helper = ReportStepsHelper

    def post(self, request, *args, **kwargs):
        self._save_report()
        return super().post(request, *args, **kwargs)

    def _save_report(self):
        self.report.encrypt_report(
            self.storage.form_data,
            self.storage.secret_key,
        )
