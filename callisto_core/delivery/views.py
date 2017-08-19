import json
import logging

import ratelimit.mixins
from nacl.exceptions import CryptoError

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils.html import conditional_escape
from django.views import generic as views
from django.core.exceptions import PermissionDenied

from . import forms, models, report_delivery
from ..utils.api import MatchingApi, NotificationApi

User = get_user_model()
logger = logging.getLogger(__name__)


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


class ReportBaseView(
    views.detail.DetailView,
):
    model = models.Report
    context_object_name = 'report'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    @property
    def report(self):
        # can only be accessed after form_valid()
        return self.object

    @property
    def site_id(self):
        return get_current_site(self.request).id

    @property
    def storage(self):
        return self.storage_helper(self)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'view': self})
        return kwargs


class ReportCreateView(
    ReportBaseView,
    views.edit.CreateView,
):
    form_class = forms.ReportCreateForm

    def get_success_url(self):
        return reverse_lazy(
            'report_update',
            kwargs={
                'step': 0,
                'uuid': self.report.uuid,
            },
        )


class ReportBaseAccessView(
    ReportBaseView,
    ratelimit.mixins.RatelimitMixin,
):
    storage_helper = SecretKeyStorageHelper
    template_name = 'callisto_core/delivery/form.html'
    invalid_access_key_message = 'Invalid key access request at {}'
    invalid_access_user_message = 'Invalid user access request at {}'
    ratelimit_key = 'user'
    ratelimit_rate = settings.DECRYPT_THROTTLE_RATE
    access_form_class = forms.ReportAccessForm
    access_template_name = template_name

    @property
    def decrypted_report(self):
        return self.report.decrypted_report(self.storage.secret_key)

    @property
    def access_granted(self):
        if settings.CALLISTO_CHECK_REPORT_OWNER:
            if not self.report.owner == self.request.user:
                self._log(self.invalid_access_user_message)
                raise PermissionDenied
        else:
            pass
        if self.storage.secret_key:
            try:
                self.decrypted_report
                return True
            except CryptoError:
                self._log(self.invalid_access_key_message)
                return False
        else:
            return False

    def dispatch(self, request, *args, **kwargs):
        if self.storage.secret_key:
            return super().dispatch(request, *args, **kwargs)
        elif self.request.POST.get('key'):
            return self._render_key_input_response()
        else:
            return self._render_access_form()

    def form_valid(self, form):
        self._set_key_from_form(form)
        return super().form_valid(form)

    def _log(self, msg):
        path = self.request.get_full_path()
        logger.warn(msg.format(path))

    def _set_key_from_form(self, form):
        if form.data.get('key'):
            self.storage.set_secret_key(form.data['key'])

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


class ReportUpdateView(
    ReportBaseAccessView,
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


class BaseReportingView(ReportUpdateView):

    def form_valid(self, form):
        output = super().form_valid(form)
        if form.cleaned_data.get('email_confirmation') == "True":
            NotificationApi.send_user_notification(
                form,
                self.email_confirmation_name,
                self.site_id,
            )
        return output


class ReportingView(BaseReportingView):
    form_class = forms.ReportingForm
    email_confirmation_name = 'submit_confirmation'

    def form_valid(self, form):
        output = super().form_valid(form)
        sent_full_report = models.SentFullReport.objects.create(
            report=self.report,
            to_address=settings.COORDINATOR_EMAIL,
        )
        NotificationApi.send_report_to_authority(
            sent_full_report,
            form.decrypted_report,
            self.site_id,
        )
        self._send_confirmation_email(form)
        return output


class MatchingView(BaseReportingView):
    form_class = forms.SubmitToMatchingForm
    email_confirmation_name = 'match_confirmation'

    def form_valid(self, form):
        output = super().form_valid(form)

        matches_for_immediate_processing = []
        for perp_form in form:
            match_report = models.MatchReport(report=self.report)

            perp_identifier = perp_form.cleaned_data.get('perp')
            match_report.contact_email = form.cleaned_data.get('email')
            match_report_content = report_delivery.MatchReportContent(
                identifier=perp_identifier,
                perp_name=conditional_escape(perp_form.cleaned_data.get('perp_name')),
                contact_name=conditional_escape(form.cleaned_data.get('name')),
                email=match_report.contact_email,
                phone=conditional_escape(form.cleaned_data.get('phone_number')),
                voicemail=conditional_escape(form.cleaned_data.get('voicemail')),
                notes=conditional_escape(form.cleaned_data.get('contact_notes')),
            )
            match_report.encrypt_match_report(
                report_text=json.dumps(match_report_content.__dict__),
                key=perp_identifier,
            )

            if settings.MATCH_IMMEDIATELY:
                # save in DB without identifier
                match_report.save()
                match_report.identifier = perp_identifier
                matches_for_immediate_processing.append(match_report)
            else:
                # temporarily save identifier in DB until matching is run
                match_report.identifier = perp_identifier
                match_report.save()

        self._send_confirmation_email(form)

        if settings.MATCH_IMMEDIATELY:
            MatchingApi.run_matching(match_reports_to_check=matches_for_immediate_processing)

        return output


class ReportActionView(ReportUpdateView):

    def get(self, request, *args, **kwargs):
        if self.access_granted:
            print('access_granted !!!')
            return self.report_action()
        else:
            print('denied XXX')
            return super().get(request, *args, **kwargs)


class MatchingWithdrawView(ReportActionView):

    def report_action(self):
        self.report.withdraw_from_matching()


class ReportDeleteView(ReportActionView):

    def report_action(self):
        print('deleting a thing')
        self.report.delete()
