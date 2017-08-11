from wizard_builder.views import StorageHelper, WizardView

from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, JsonResponse
from django.utils.crypto import get_random_string

from . import security
from .hashers import get_hasher, make_key
from .models import Report


class EncryptedStorageHelper(StorageHelper):

    @property
    def form_data(self):
        return self.decrypt(super().form_data)

    @property
    def post_data(self):
        return self.encrypt(super().post_data)

    @property
    def secret_key(self):
        return ''

    @property
    def encode_prefix(self):
        return self.view.request.session['encode_prefix']

    def set_encode_prefix(self, prefix):
        self.view.request.session['encode_prefix'] = prefix

    def encrypt(self, data):
        hasher = get_hasher()
        encoded = hasher.encode(self.secret_key, get_random_string())
        encode_prefix, stretched_key = hasher.split_encoded(encoded)
        self.set_encode_prefix(encode_prefix)
        return security.encrypt_text(stretched_key, data)

    def decrypt(self, data):
        _, stretched_key = make_key(self.encode_prefix, self.secret_key, '')
        return security.decrypt_text(stretched_key, data)


class EncryptedWizardView(WizardView):
    storage_helper = EncryptedStorageHelper

    @property
    def report(self):
        return Report(owner=self.request.user)

    def render_key_creation(self, **kwargs):
        return HttpResponseRedirect(reverse('key_creation'))

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
