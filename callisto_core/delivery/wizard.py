from wizard_builder.views import StorageHelper, WizardView

from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, JsonResponse

from .models import Report


class EncryptedStorageHelper(StorageHelper):

    @property
    def secret_key(self):
        return ''


class EncryptedWizardView(WizardView):

    @property
    def report(self):
        return Report(owner=self.request.user)

    def render_key_creation(self, **kwargs):
        return HttpResponseRedirect(reverse('key_creation'))

    def render_finished(self, **kwargs):
        self._save_report()
        return JsonResponse(self.report)

    def render_done(self, **kwargs):
        return self.render_finished(**kwargs)

    def dispatch(self, request, step=None, *args, **kwargs):
        if self.storage.secret_key:
            self._save_report()
            return super().dispatch(request, *args, **kwargs)
        else:
            return self.render_key_creation(**kwargs)

    def _save_report(self):
        self.report.encrypt_report(
            self.storage.get_form_data,
            self.storage.secret_key,
        )
