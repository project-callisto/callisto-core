from wizard_builder.views import StorageHelper, WizardView

from django.core.urlresolvers import reverse_lazy
from django.http.response import JsonResponse
from django.views import generic as views

from .models import Report
from .views import SecretKeyView


class RedirectWizardView(views.base.RedirectView):
    url = reverse_lazy(
        'wizard_view',
        kwargs={'step': 0, 'report_id': 0},
    )


class _EncryptedStorageHelper(StorageHelper):

    @property
    def form_data(self):
        return self.decrypt(super().form_data)

    @property
    def post_data(self):
        return self.encrypt(super().post_data)

    @property
    def secret_key(self):
        return ''

    def encrypt(self, data):
        return data  # TODO

    def decrypt(self, data):
        return data  # TODO


class _ReportUpdateView(SecretKeyView, views.edit.BaseUpdateView):
    pass


class EncryptedWizardView(_ReportUpdateView, WizardView):
    storage_helper = _EncryptedStorageHelper

    @property
    def report(self):
        return Report(owner=self.request.user)

    def render_finished(self, **kwargs):
        self._save_report()
        return JsonResponse(self.report)

    def dispatch(self, request, step=None, *args, **kwargs):
        if self.storage.secret_key:
            self._save_report()
            return super().dispatch(request, *args, **kwargs)
        else:
            return self.render_key_creation(**kwargs)

    def _save_report(self):
        self.report.encrypt_report(
            self.storage.form_data,
            self.storage.secret_key,
        )
