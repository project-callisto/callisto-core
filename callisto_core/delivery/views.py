import json
import logging

import ratelimit.mixins
from nacl.exceptions import CryptoError

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.utils.html import conditional_escape
from django.views import generic as views

from . import forms, models
from ..evaluation.models import EvalRow
from ..utils.api import MatchingApi, NotificationApi
from .models import MatchReport, SentFullReport
from .report_delivery import MatchReportContent, PDFFullReport

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


class ReportBaseView(views.edit.ModelFormMixin):
    model = models.Report
    storage_helper = SecretKeyStorageHelper
    template_name = 'callisto_core/delivery/form.html'
    context_object_name = 'report'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    @property
    def site_id(self):
        return get_current_site(self.request).id

    @property
    def storage(self):
        return self.storage_helper(self)

    def _set_key_from_form(self, form):
        if form.data.get('key'):
            self.storage.set_secret_key(form.data['key'])

    def form_valid(self, form):
        self._set_key_from_form(form)
        return super().form_valid(form)


class ReportCreateView(
    ReportBaseView,
    views.edit.CreateView,
):
    form_class = forms.ReportCreateForm

    @property
    def report(self):
        # can only be accessed after form_valid()
        return self.object

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
    views.edit.UpdateView,
    ratelimit.mixins.RatelimitMixin,
):
    invalid_access_message = 'Invalid access request at url {}'
    ratelimit_key = 'user'
    ratelimit_rate = settings.DECRYPT_THROTTLE_RATE
    ratelimit_block = True
    ratelimit_method = 'POST'

    @property
    def report(self):
        # can be accessed at any point
        return self.get_object()

    @property
    def access_granted(self):
        if self.storage.secret_key:
            try:
                self.report.decrypted_report(self.storage.secret_key)
                return True
            except CryptoError:
                self._log_invalid_access()
        return False

    def _log_invalid_access(self):
        logger.info(self.invalid_access_message.format(
            self.request.get_full_path()))


class ReportFormAccessView(ReportBaseAccessView):
    access_form_class = forms.ReportAccessForm

    def dispatch(self, request, *args, **kwargs):
        if self.storage.secret_key:
            EvalRow.store_eval_row(action=EvalRow.VIEW, report=self.report)
            return super().dispatch(request, *args, **kwargs)
        else:
            return views.edit.UpdateView.dispatch(
                self, request, *args, **kwargs)

    def get_success_url(self):
        return self.request.path

    def get_form(self, form_class=None):
        if self.storage.secret_key:
            return super().get_form()
        else:
            self._log_invalid_access()
            return self.access_form_class(**self.get_form_kwargs())


class BaseReportingView(ReportFormAccessView):

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
    # was submit_report_to_authority
    form_class = forms.SubmitReportToAuthorityForm

    def form_valid(self, form):
        output = super().form_valid(form)
        EvalRow.store_eval_row(action=EvalRow.SUBMIT, report=self.report)
        sent_full_report = SentFullReport.objects.create(
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
    # was submit_to_matching
    form_class = forms.SubmitToMatchingFormSet
    email_confirmation_name = 'match_confirmation'

    def form_valid(self, form):
        output = super().form_valid(form)

        matches_for_immediate_processing = []
        for perp_form in form:
            # enter into matching
            match_report = MatchReport(report=self.report)

            perp_identifier = perp_form.cleaned_data.get('perp')
            match_report.contact_email = form.cleaned_data.get('email')
            match_report_content = \
                MatchReportContent(identifier=perp_identifier,
                                   perp_name=conditional_escape(perp_form.cleaned_data.get('perp_name')),
                                   contact_name=conditional_escape(form.cleaned_data.get('name')),
                                   email=match_report.contact_email,
                                   phone=conditional_escape(form.cleaned_data.get('phone_number')),
                                   voicemail=conditional_escape(form.cleaned_data.get('voicemail')),
                                   notes=conditional_escape(form.cleaned_data.get('contact_notes')))
            match_report.encrypt_match_report(report_text=json.dumps(match_report_content.__dict__),
                                              key=perp_identifier)

            if settings.MATCH_IMMEDIATELY:
                # save in DB without identifier
                match_report.save()
                match_report.identifier = perp_identifier
                matches_for_immediate_processing.append(match_report)
            else:
                # temporarily save identifier in DB until matching is run
                match_report.identifier = perp_identifier
                match_report.save()

            # record matching submission in anonymous evaluation data
            EvalRow.store_eval_row(action=EvalRow.MATCH, report=self.report, match_identifier=perp_identifier)

        self._send_confirmation_email(form)

        if settings.MATCH_IMMEDIATELY:
            MatchingApi.run_matching(match_reports_to_check=matches_for_immediate_processing)

        return output


class ReportActionView(ReportBaseAccessView):

    def get(self, request, *args, **kwargs):
        if self.access_granted:
            return self.report_action()
        else:
            return super().post(request, *args, **kwargs)


class MatchingWithdrawView(ReportActionView):
    # was withdraw_from_matching

    def report_action(self):
        self.report.withdraw_from_matching()


class ReportDeleteView(ReportActionView):
    # was delete_report

    def report_action(self):
        self.report.delete()


class ReportPDFView(ReportActionView):

    def report_action(self):
        response = HttpResponse(content_type='application/pdf')
        response.update({
            'Content-Disposition': 'inline; filename="report.pdf"',
        })
        pdf = PDFFullReport(
            report=self.report,
            decrypted_report=self.form.decrypted_report,
        ).generate_pdf_report(
            recipient=None,
            report_id=None,
        )
        response.write(pdf)
        return response
