import logging

import ratelimit.mixins
from nacl.exceptions import CryptoError

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.views import generic as views

from wizard_builder import views as wizard_builder_views

from . import fields, forms, models, view_helpers

logger = logging.getLogger(__name__)


# TODO: generalize all of these to be about Model / Object, rather than Report
# the intent there being more effective use of django builtin functionality


class ReportBasePartial(
    wizard_builder_views.WizardFormPartial,
):
    model = models.Report
    storage_helper = view_helpers.EncryptedReportStorageHelper
    template_name = 'callisto_core/delivery/form.html'

    @property
    def site_id(self):
        # TODO: remove
        return get_current_site(self.request).id

    @property
    def decrypted_report(self):
        return self.report.decrypted_report(self.storage.secret_key)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'view': self})
        return kwargs


# TODO: rename all of these to end in Partial, not View


class __ReportDetailView(
    ReportBasePartial,
    views.detail.DetailView,
):
    context_object_name = 'report'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    @property
    def report(self):
        # TODO: remove, use self.object
        return self.get_object()


class __ReportLimitedDetailView(
    __ReportDetailView,
    ratelimit.mixins.RatelimitMixin,
):
    ratelimit_key = 'user'
    ratelimit_rate = settings.DECRYPT_THROTTLE_RATE


class __ReportAccessView(
    __ReportLimitedDetailView,
):
    valid_access_message = 'Valid access request at {}'
    invalid_access_key_message = 'Invalid (key) access request at {}'
    invalid_access_user_message = 'Invalid (user) access request at {}'
    invalid_access_no_key_message = 'Invalid (no key) access request at {}'
    access_form_class = forms.ReportAccessForm
    access_template_name = ReportBasePartial.template_name

    @property
    def access_granted(self):
        self._check_report_owner()
        if self.storage.secret_key:
            try:
                self.decrypted_report
                # TODO: self.log.info('Valid access')
                self._log_info(self.valid_access_message)
                return True
            except CryptoError:
                self._log_warn(self.invalid_access_key_message)
                return False
        else:
            self._log_info(self.invalid_access_no_key_message)
            return False

    @property
    def access_form_valid(self):
        form = self._get_access_form()
        if form.is_valid():
            # TODO: dont hardcode passphrase POST arg
            self.storage.set_secret_key(self.request.POST.get('key'))
            return True
        else:
            return False

    @property
    def object_form_valid(self):
        self.object = self.report
        form = self.get_form()
        return form.is_valid()

    @property
    def object_form_has_passphrase(self):
        form = self.get_form()
        for field_name, field_object in form.fields.items():
            if (
                field_name == 'key' and
                isinstance(field_object, fields.PassphraseField)
            ):
                return True

    @property
    def pass_access_through(self):
        return bool(
            self.access_form_valid and
            self.object_form_valid and
            self.object_form_has_passphrase
        )

    def dispatch(self, request, *args, **kwargs):
        if self.storage.secret_key or self.pass_access_through:
            return super().dispatch(request, *args, **kwargs)
        elif self.access_form_valid:
            return HttpResponseRedirect(self.request.path)
        else:
            return self._render_access_form()

    def _get_access_form(self):
        form_kwargs = self.get_form_kwargs()
        form_kwargs.update({'instance': self.get_object()})
        return self.access_form_class(**form_kwargs)

    def _render_access_form(self):
        self.object = self.report
        self.template_name = self.access_template_name
        context = self.get_context_data(form=self._get_access_form())
        return self.render_to_response(context)

    def _check_report_owner(self):
        if settings.CALLISTO_CHECK_REPORT_OWNER:
            if not self.report.owner == self.request.user:
                self._log_warn(self.invalid_access_user_message)
                raise PermissionDenied

    def _log_info(self, msg):
        # TODO: LoggingHelper
        self._log(msg, logger.info)

    def _log_warn(self, msg):
        # TODO: LoggingHelper
        self._log(msg, logger.warn)

    def _log(self, msg, log):
        # TODO: LoggingHelper
        path = self.request.get_full_path()
        log(msg.format(path))


class ReportUpdateView(
    __ReportAccessView,
    views.edit.UpdateView,
):

    @property
    def report(self):
        # TODO: remove, use self.object
        return self.get_object()


class ReportActionView(
    ReportUpdateView,
):
    success_url = '/'
    form_class = forms.ReportAccessForm

    def form_valid(self, form):
        output = super().form_valid(form)
        self.view_action()
        self.storage.clear_secret_key()
        return output

    def view_action(self):
        pass
