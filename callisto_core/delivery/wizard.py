import logging

from wizard_builder.view_helpers import StepsHelper, StorageHelper
from wizard_builder.views import WizardView

from django.core.urlresolvers import reverse
from django.http import HttpResponse

from .views import (
    ReportActionView, ReportFormAccessView, SecretKeyStorageHelper,
)

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

    @property
    def report(self):
        return self.view.report

    def current_data_from_storage(self):
        if self.secret_key:
            return self.report.decrypted_report(self.secret_key)
        else:
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

    def dispatch(self, request, step=None, *args, **kwargs):
        self._dispatch_processing(step)
        return super().dispatch(request, step=step, *args, **kwargs)


class WizardAccessActionView(
    ReportActionView,
    EncryptedWizardView,
):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(
            request, step=StepsHelper.done_name, *args, **kwargs)


class ReportPDFView(WizardAccessActionView):

    def report_action(self):
        return self._report_pdf_response()

    def _report_pdf_response(self):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="report.pdf"'
        response.write(self.report.as_pdf(
            data=self.storage.cleaned_form_data,
            recipient=None,
        ))
        return response
