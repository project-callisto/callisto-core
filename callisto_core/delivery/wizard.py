from wizard_builder.views import StorageHelper, WizardView

from django.http.response import JsonResponse

from .models import Report
from .views import ReportAccessView, SecretKeyStorageHelper


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

    def render_finished(self, **kwargs):
        return JsonResponse(self.report)

    def post(self, request, *args, **kwargs):
        self._save_report()
        return super().post(request, *args, **kwargs)

    def _save_report(self):
        self.report.encrypt_report(
            self.storage.form_data,
            self.storage.secret_key,
        )
