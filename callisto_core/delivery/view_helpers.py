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
            return self.report.decrypted_report(
                self.secret_key).get('data', {})
        else:
            return {'data': {}}

    def add_data_to_storage(self, data):
        data = {'data': data}
        self.report.encrypt_report(data, self.secret_key)
