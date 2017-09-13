import logging

from django.core.urlresolvers import reverse

from wizard_builder import view_helpers as wizard_builder_view_helpers

logger = logging.getLogger(__name__)


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


class _SecretKeyStorageHelper(object):

    def set_secret_key(self, key):
        self.view.request.session['secret_key'] = key

    def clear_secret_key(self):
        del self.view.request.session['secret_key']

    @property
    def report(self):
        try:
            return self.view.report
        except BaseException:
            # TODO: catch models.Report.DoesNotExist ?
            return None

    @property
    def secret_key(self):
        return self.view.request.session.get('secret_key')

    @property
    def decrypted_report(self):
        return self.report.decrypted_report(self.secret_key)

    @property
    def report_and_key_present(self):
        return bool(self.secret_key and getattr(self, 'report', None))


class _LegacyEncryptedStorageHelper(
    _SecretKeyStorageHelper,
):

    def _initialize_storage(self):
        if not self.report.encrypted:
            self._create_new_report_storage()
        elif self._report_is_legacy_format():
            self._translate_legacy_report_storage()
        else:
            pass  # storage already initialized

    def _report_is_legacy_format(self):
        decrypted_report = self.report.decrypted_report(self.secret_key)
        is_legacy = bool(
            not decrypted_report.get(
                self.storage_form_key, False))
        return is_legacy

    def _create_new_report_storage(self):
        self.report.encryption_setup(self.secret_key)
        self._create_storage({})

    def _translate_legacy_report_storage(self):
        decrypted_report = self.report.decrypted_report(self.secret_key)
        self._create_storage(decrypted_report[self.storage_data_key])
        logger.debug('translated legacy report storage')

    def _create_storage(self, data):
        storage = {
            self.storage_data_key: data,
            self.storage_form_key: self.view.get_serialized_forms(),
        }
        self.report.encrypt_report(storage, self.secret_key)


class EncryptedStorageHelper(
    _LegacyEncryptedStorageHelper,
    wizard_builder_view_helpers.StorageHelper,
):
    storage_data_key = 'data'

    def current_data_from_storage(self):
        if self.report_and_key_present:
            return self.report.decrypted_report(self.secret_key)
        else:
            return {
                self.storage_data_key: {},
                self.storage_form_key: {},
            }

    def add_data_to_storage(self, data):
        if self.report_and_key_present:
            storage = self.current_data_from_storage()
            storage[self.storage_data_key] = data
            self.report.encrypt_report(storage, self.secret_key)

    def init_storage(self):
        if self.report_and_key_present:
            self._initialize_storage()
