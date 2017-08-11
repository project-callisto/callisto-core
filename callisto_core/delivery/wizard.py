import json
import logging

from wizard_builder.views import StorageHelper, WizardView

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from ..evaluation.models import EvalRow
from .forms import NewSecretKeyForm, SecretKeyForm
from .models import Report

logger = logging.getLogger(__name__)


class EncryptedStorageHelper(StorageHelper):

    @property
    def secret_key(self):
        return ''


class EncryptedWizardView(WizardView):

    @classmethod
    def get_key_form(cls):
        return NewSecretKeyForm

    @property
    def report(self):
        return Report(owner=self.request.user)

    def _save_report(self):
        self.report.encrypt_report(
            self.storage.get_form_data,
            self.storage.secret_key,
            self.object_to_edit,
        )

    def render_key_creation(self, **kwargs):
        return HttpResponseRedirect(reverse('key_creation'))

    def render_finished(self, **kwargs):
        self._save_report()
        return HttpResponse(self.report)

    def render_done(self, **kwargs):
        return self.render_finished(report, **kwargs)

    def dispatch(self, request, step=None, *args, **kwargs):
        if self.storage.secret_key:
            self._save_report()
            return super().dispatch(request, *args, **kwargs)
        else:
            return self.render_key_creation(**kwargs)
