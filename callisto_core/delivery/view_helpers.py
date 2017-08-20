from django.core.urlresolvers import reverse

from wizard_builder import view_helpers as wizard_builder_view_helpers


class SecretKeyStorageHelper(object):

    def __init__(self, view):
        self.view = view

    def set_secret_key(self, key):
        self.view.request.session['secret_key'] = key

    @property
    def report(self):
        return self.view.report

    @property
    def secret_key(self):
        return self.view.request.session.get('secret_key')


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
    SecretKeyStorageHelper,
    wizard_builder_view_helpers.StorageHelper,
):

    @property
    def report(self):
        return self.view.report

    def current_data_from_storage(self):
        if self.secret_key:
            return self.report.decrypted_report(
                self.secret_key).get('data', {})
        else:
            return {'data': {}}

    def add_data_to_storage(self, data):
        data = {'data': data}
        self.report.encrypt_report(data, self.secret_key)
