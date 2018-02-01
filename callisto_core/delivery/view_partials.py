'''

View partials provide all the callisto-core front-end functionality.
Subclass these partials with your own views if you are implementing
callisto-core. Many of the view partials only provide a subset of the
functionality required for a full HTML view.

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/
    - https://github.com/project-callisto/callisto-core/blob/master/callisto_core/wizard_builder/view_partials.py

view_partials should define:
    - forms
    - models
    - helper classes
    - access checks
    - redirect handlers

and should not define:
    - templates
    - url names

'''
import logging
import re

import ratelimit.mixins
from nacl.exceptions import CryptoError

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import generic as views

from callisto_core.evaluation.view_partials import EvalDataMixin
from callisto_core.reporting import report_delivery
from callisto_core.wizard_builder import (
    view_partials as wizard_builder_partials,
)

from . import forms, models, view_helpers

logger = logging.getLogger(__name__)


#######################
# secret key partials #
#######################


class _PassphrasePartial(
    views.base.TemplateView,
):
    storage_helper = view_helpers.ReportStorageHelper

    @property
    def storage(self):
        return self.storage_helper(self)


class _PassphraseClearingPartial(
    EvalDataMixin,
    _PassphrasePartial,
):

    def get(self, request, *args, **kwargs):
        self.storage.clear_passphrases()
        return super().get(request, *args, **kwargs)


class DashboardPartial(
    _PassphraseClearingPartial,
):
    EVAL_ACTION_TYPE = 'DASHBOARD'


###################
# report partials #
###################


class ReportBasePartial(
    EvalDataMixin,
    wizard_builder_partials.WizardFormPartial,
):
    model = models.Report
    storage_helper = view_helpers.EncryptedReportStorageHelper
    EVAL_ACTION_TYPE = 'VIEW'

    @property
    def site_id(self):
        # TODO: remove
        return self.request.site.id

    @property
    def decrypted_report(self):
        return self.report.decrypt_record(self.storage.passphrase)

    def get_form_kwargs(self):
        # TODO: remove
        kwargs = super().get_form_kwargs()
        kwargs.update({'view': self})
        return kwargs


class ReportCreatePartial(
    ReportBasePartial,
    views.edit.CreateView,
):
    form_class = forms.ReportCreateForm
    EVAL_ACTION_TYPE = 'CREATE'

    def get_success_url(self):
        return reverse(
            self.success_url,
            kwargs={'step': 0, 'uuid': self.object.uuid},
        )


class _ReportDetailPartial(
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


class _ReportLimitedDetailPartial(
    _ReportDetailPartial,
    ratelimit.mixins.RatelimitMixin,
):
    ratelimit_key = 'user'
    ratelimit_rate = settings.DECRYPT_THROTTLE_RATE


class _ReportAccessPartial(
    _ReportLimitedDetailPartial,
):
    invalid_access_key_message = 'Invalid key in access request'
    invalid_access_user_message = 'Invalid user in access request'
    invalid_access_no_key_message = 'No key in access request'
    form_class = forms.ReportAccessForm
    access_form_class = forms.ReportAccessForm

    @property
    def access_granted(self):
        self._check_report_owner()
        if self.storage.passphrase:
            try:
                self.decrypted_report
                return True
            except CryptoError:
                logger.warn(self.invalid_access_key_message)
                return False
        else:
            logger.info(self.invalid_access_no_key_message)
            return False

    @property
    def access_form_valid(self):
        form = self._get_access_form()
        if form.is_valid():
            form.save()
            return True
        else:
            return False

    def _passphrase_next_url(self, request):
        next_url = None
        if 'next' in request.GET:
            if re.search('^/[\W/-]*', request.GET['next']):
                next_url = request.GET['next']
        return next_url

    def dispatch(self, request, *args, **kwargs):
        logger.debug(f'{self.__class__.__name__} access check')

        if (self.access_granted or self.access_form_valid) and self._passphrase_next_url(
                request):
            return self._redirect_from_passphrase(request)
        elif self.access_granted or self.access_form_valid:
            return super().dispatch(request, *args, **kwargs)
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

    def _redirect_from_passphrase(self, request):
        return redirect(self._passphrase_next_url(request))

    def _check_report_owner(self):
        if not self.report.owner == self.request.user:
            logger.warn(self.invalid_access_user_message)
            raise PermissionDenied


class _ReportUpdatePartial(
    _ReportAccessPartial,
    views.edit.UpdateView,
):
    back_url = None

    @property
    def report(self):
        # TODO: remove, use self.object
        return self.get_object()


###################
# wizard partials #
###################


class EncryptedWizardPartial(
    _ReportUpdatePartial,
    wizard_builder_partials.WizardPartial,
):
    steps_helper = view_helpers.ReportStepsHelper
    EVAL_ACTION_TYPE = 'EDIT'

    def dispatch(self, request, *args, **kwargs):
        self._dispatch_processing()
        return super().dispatch(request, *args, **kwargs)

    def _rendering_done_hook(self):
        self.eval_action('REVIEW')


###################
# report actions  #
###################


class _ReportActionPartial(
    _ReportUpdatePartial,
):
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        logger.debug(f'{self.__class__.__name__} form valid')
        output = super().form_valid(form)
        self.view_action()
        return output

    def form_invalid(self, form):
        return super().form_invalid(form)

    def view_action(self):
        pass


class ReportDeletePartial(
    _ReportActionPartial,
):
    EVAL_ACTION_TYPE = 'DELETE'

    def view_action(self):
        self.report.delete()


class WizardPDFPartial(
    _ReportActionPartial,
):
    EVAL_ACTION_TYPE = 'ACCESS_PDF'

    def form_valid(self, form):
        super().form_valid(form)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = self.content_disposition + \
            '; filename="report.pdf"'
        response.write(report_delivery.report_as_pdf(
            report=self.report,
            data=self.storage.cleaned_form_data,
            recipient=None,
        ))
        return response


class ViewPDFPartial(
    WizardPDFPartial,
):
    content_disposition = 'inline'
    EVAL_ACTION_TYPE = 'VIEW_PDF'


class DownloadPDFPartial(
    WizardPDFPartial,
):
    content_disposition = 'attachment'
    EVAL_ACTION_TYPE = 'DOWNLOAD_PDF'
