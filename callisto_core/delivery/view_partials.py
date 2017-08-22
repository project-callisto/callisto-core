import logging

import ratelimit.mixins
from nacl.exceptions import CryptoError

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views import generic as views

from . import forms, models, view_helpers

logger = logging.getLogger(__name__)


class ReportBaseMixin(object):
    model = models.Report
    storage_helper = view_helpers.SecretKeyStorageHelper
    template_name = 'callisto_core/delivery/form.html'

    @property
    def site_id(self):
        return get_current_site(self.request).id

    @property
    def storage(self):
        return self.storage_helper(self)

    @property
    def report(self):
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'view': self})
        return kwargs


class ReportDetailView(
    ReportBaseMixin,
    views.detail.DetailView,
):
    context_object_name = 'report'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'


class ReportLimitedDetailView(
    ReportDetailView,
    ratelimit.mixins.RatelimitMixin,
):
    ratelimit_key = 'user'
    ratelimit_rate = settings.DECRYPT_THROTTLE_RATE


class ReportAccessView(
    ReportLimitedDetailView,
):
    valid_access_message = 'Valid access request at {}'
    invalid_access_key_message = 'Invalid (key) access request at {}'
    invalid_access_user_message = 'Invalid (user) access request at {}'
    invalid_access_no_key_message = 'Invalid (no key) access request at {}'
    access_form_class = forms.ReportAccessForm
    access_template_name = ReportBaseMixin.template_name

    @property
    def decrypted_report(self):
        return self.report.decrypted_report(self.storage.secret_key)

    @property
    def access_granted(self):
        if settings.CALLISTO_CHECK_REPORT_OWNER:
            if not self.report.owner == self.request.user:
                self._log_warn(self.invalid_access_user_message)
                raise PermissionDenied
        else:
            pass
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

    def dispatch(self, request, *args, **kwargs):
        if self.storage.secret_key:
            return super().dispatch(request, *args, **kwargs)
        elif self.request.POST.get('key'):
            return self._render_key_input_response()
        else:
            return self._render_access_form()

    def _render_key_input_response(self):
        form = self.access_form_class(**self.get_form_kwargs())
        if form.is_valid():
            self.storage.set_secret_key(self.request.POST.get('key'))
            return HttpResponseRedirect(self.request.path)
        else:
            return self._render_access_form(form)

    def _render_access_form(self, form=None):
        self.object = self.report
        self.template_name = self.access_template_name
        if not form:
            form = self.access_form_class(**self.get_form_kwargs())
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

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
    ReportAccessView,
    views.edit.UpdateView,
):

    @property
    def report(self):
        # can be accessed at any point
        return self.get_object()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': self.report})
        return kwargs


class ReportActionView(
    ReportUpdateView,
):

    def get(self, request, *args, **kwargs):
        if self.access_granted:
            self._report_action()
            return self._action_response()
        else:
            return super().get(request, *args, **kwargs)

    def _report_action(self):
        # TODO: implement as a helper
        pass

    def _action_response(self):
        return self._redirect_to_done()

    def _redirect_to_done(self):
        return HttpResponseRedirect(reverse(
            'report_view',
            kwargs={'uuid': self.report.uuid},
        ))
