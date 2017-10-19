'''

View partials provide all the callisto-core front-end functionality.
Subclass these partials with your own views if you are implementing
callisto-core. Many of the view partials only provide a subset of the
functionality required for a full HTML view.

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/
    - https://github.com/SexualHealthInnovations/django-wizard-builder/blob/master/wizard_builder/view_partials.py

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

import ratelimit.mixins
from nacl.exceptions import CryptoError

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic as views

from wizard_builder import view_partials as wizard_builder_partials

from . import forms, models, view_helpers
from ..reporting import report_delivery

logger = logging.getLogger(__name__)


#######################
# secret key partials #
#######################


class SecretKeyTemplatePartial(
    views.base.TemplateView,
):
    storage_helper = view_helpers.SecretKeyStorageHelper

    @property
    def storage(self):
        return self.storage_helper(self)


class KeyResetTemplatePartial(
    SecretKeyTemplatePartial,
):

    def dispatch(self, request, *args, **kwargs):
        self.storage.clear_secret_key()
        return super().dispatch(request, *args, **kwargs)


###################
# report partials #
###################


# TODO: generalize all of these to be about Model / Object, rather than Report
# the intent there being more effective use of django builtin functionality


class ReportBasePartial(
    wizard_builder_partials.WizardFormPartial,
):
    model = models.Report
    storage_helper = view_helpers.EncryptedReportStorageHelper

    @property
    def site_id(self):
        # TODO: remove
        return get_current_site(self.request).id

    @property
    def decrypted_report(self):
        return self.report.decrypted_report(self.storage.secret_key)

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
        if self.storage.secret_key:
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

    def dispatch(self, request, *args, **kwargs):
        if self.access_granted:
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
                logger.warn(self.invalid_access_user_message)
                raise PermissionDenied


class ReportUpdatePartial(
    _ReportAccessPartial,
    views.edit.UpdateView,
):
    back_url = None

    @property
    def report(self):
        # TODO: remove, use self.object
        return self.get_object()


class ReportActionPartial(
    ReportUpdatePartial,
):
    success_url = '/'

    def form_valid(self, form):
        output = super().form_valid(form)
        self.view_action()
        self.storage.clear_secret_key()
        return output

    def view_action(self):
        pass


class ReportDeletePartial(
    ReportActionPartial,
):

    def view_action(self):
        self.report.delete()


###################
# wizard partials #
###################


class EncryptedWizardPartial(
    ReportUpdatePartial,
    wizard_builder_partials.WizardPartial,
):
    steps_helper = view_helpers.ReportStepsHelper

    def dispatch(self, request, *args, **kwargs):
        self._dispatch_processing()
        return super().dispatch(request, *args, **kwargs)


class WizardActionPartial(
    EncryptedWizardPartial,
):
    access_form_class = forms.ReportAccessForm

    def dispatch(self, request, *args, **kwargs):
        self._dispatch_processing()
        self.kwargs['step'] = view_helpers.ReportStepsHelper.done_name
        if self.access_granted:
            return self.view_action()
        else:
            return self._render_access_form()


class WizardPDFPartial(
    WizardActionPartial,
):

    def view_action(self):
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


class DownloadPDFPartial(
    WizardPDFPartial,
):
    content_disposition = 'attachment'
