from django.core.urlresolvers import reverse

from wizard_builder import view_helpers as wizard_builder_view_helpers


class _SecretKeyStorageHelper(object):

    def __init__(self, view):
        self.view = view

    def set_secret_key(self, key):
        self.view.request.session['secret_key'] = key

    def clear_secret_key(self):
        del self.view.request.session['secret_key']

    @property
    def report(self):
        return self.view.report

    @property
    def secret_key(self):
        return self.view.request.session.get('secret_key')

    @property
    def decrypted_report(self):
        return self.report.decrypted_report(self.secret_key)


class ReportStepsHelper(
    wizard_builder_view_helpers.StepsHelper,
):

    def url(self, step):
        return reverse(
            self.view.request.resolver_match.view_name,
            kwargs={
                'step': step,
                'uuid': self.view.report.uuid,
            },
        )


class EncryptedStorageHelper(
    _SecretKeyStorageHelper,
    wizard_builder_view_helpers.StorageHelper,
):

    def current_data_from_storage(self):
        if self.secret_key and getattr(self, 'report', None):
            self.init_storage()  # TODO: __init__ should be calling this???
            return self.report.decrypted_report(self.secret_key)
        else:
            return {
                self.storage_data_key: {},
                self.storage_form_key: {},
            }

    def add_data_to_storage(self, data):
        if self.secret_key and getattr(self, 'report', None):
            storage = self.current_data_from_storage()
            storage[self.storage_data_key] = data
            self.report.encrypt_report(storage, self.secret_key)

    def init_storage(self):
        if (
            self.secret_key and
            getattr(self, 'report', None) and
            not self.report.encrypted
        ):
            self.report.encryption_setup(self.secret_key)
            storage = {
                self.storage_data_key: {},
                self.storage_form_key: self.view.get_serialized_forms(),
            }
            self.report.encrypt_report(storage, self.secret_key)
