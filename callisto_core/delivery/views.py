import json
import logging

import ratelimit
from ratelimit.mixins import RatelimitMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import conditional_escape
from django.views import generic as views

from . import forms, models
from ..evaluation.models import EvalRow
from ..utils.api import MatchingApi, NotificationApi
from .models import MatchReport, Report, SentFullReport
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
            'wizard_update',
            kwargs={
                'step': 0,
                'uuid': self.report.uuid,
            },
        )


class ReportAccessView(
    ReportBaseView,
    views.edit.UpdateView,
    ratelimit.mixins.RatelimitMixin,
):
    access_form_class = forms.ReportAccessForm
    invalid_access_message = 'Invalid access request at url {}'
    ratelimit_key = 'user'
    ratelimit_rate = settings.DECRYPT_THROTTLE_RATE
    ratelimit_block = True
    ratelimit_method = 'POST'

    @property
    def report(self):
        # can be accessed at any point
        return self.get_object()

    def post(self, request, *args, **kwargs):
        if self.storage.secret_key:
            return super().post(request, *args, **kwargs)
        else:
            return views.edit.UpdateView.post(
                self, request, *args, **kwargs)

    def get_success_url(self):
        return self.request.path

    def get_form(self, form_class=None):
        if self.storage.secret_key:
            return super().get_form()
        else:
            self._log_invalid_access()
            return self.access_form_class(**self.get_form_kwargs())

    def _log_invalid_access(self):
        logger.info(self.invalid_access_message.format(
            self.request.get_full_path()))


class BaseReportingView(ReportAccessView):

    def _send_confirmation_email(self, form):
        if form.cleaned_data.get('email_confirmation') == "True":
            NotificationApi.send_user_notification(
                form, self.email_confirmation_name, site.id)

# submit_report_to_authority
class ReportingView(BaseReportingView):
    form_class = forms.SubmitReportToAuthorityForm
    email_confirmation_name = 'submit_confirmation'

    def form_valid(self, form):
        output = super().form_valid(form)
        sent_full_report = SentFullReport.objects.create(
            report=report, to_address=settings.COORDINATOR_EMAIL)
        NotificationApi.send_report_to_authority(
            sent_full_report, form.decrypted_report, site.id)
        EvalRow.store_eval_row(action=EvalRow.SUBMIT, report=report)
        self._send_confirmation_email(form)
        return output


# submit_to_matching
class MatchingView(BaseReportingView):
    form_class = forms.SubmitToMatchingForm
    email_confirmation_name = 'match_confirmation'

    def form_valid(self, form):
        output = super().form_valid(form)

        matches_for_immediate_processing = []
        for perp_form in formset:
            # enter into matching
            match_report = MatchReport(report=report)

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
            EvalRow.store_eval_row(action=EvalRow.MATCH, report=report, match_identifier=perp_identifier)

        self._send_confirmation_email(form)

        if settings.MATCH_IMMEDIATELY:
            MatchingApi.run_matching(match_reports_to_check=matches_for_immediate_processing)

        return output


def withdraw_from_matching(request, report_id, template_name, extra_context=None):
    report = Report.objects.get(id=report_id)
    owner = report.owner
    context = {'owner': owner, 'report': report, **extra_context}

    report.withdraw_from_matching()
    report.save()
    # record match withdrawal in anonymous evaluation data
    EvalRow.store_eval_row(action=EvalRow.WITHDRAW, report=report)

    context.update({'match_report_withdrawn': True})
    return render(request, template_name, context)


def export_as_pdf(
    request,
    report_id,
    force_download=True,
    filename='report.pdf',
    template_name='export_report.html',
    extra_context=None
):
    report = Report.objects.get(id=report_id)
    owner = report.owner
    context = {'owner': owner, 'report': report, **extra_context}

    if request.method == 'POST':
        form = forms.ReportAccessForm(request.POST)
        form.report = report
        if form.is_valid():
            EvalRow.store_eval_row(action=EvalRow.VIEW, report=report)
            try:
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = '{}; filename="{}"'\
                    .format('attachment' if force_download else 'inline', filename)
                pdf = PDFFullReport(report=report, decrypted_report=form.decrypted_report)\
                    .generate_pdf_report(recipient=None, report_id=None)
                response.write(pdf)
                return response
            except Exception:
                logger.exception("could not export report {}".format(report_id))
                form.add_error(None, "There was an error exporting your report.")
    else:
        form = forms.ReportAccessForm()
        form.report = report
    context.update({'form': form})
    return render(request, template_name, context)


def delete_report(
    request,
    report_id,
    form_template_name='delete_report.html',
    confirmation_template='delete_report.html',
    extra_context=None
):
    report = Report.objects.get(id=report_id)
    owner = report.owner
    context = {'owner': owner, 'report': report, **extra_context}

    if request.method == 'POST':
        form = forms.ReportAccessForm(request.POST)
        form.report = report
        if form.is_valid():
            EvalRow.store_eval_row(action=EvalRow.DELETE, report=report)
            try:
                report.delete()
                context.update({'report_deleted': True})
                return render(request, confirmation_template, context)
            except Exception:
                logger.exception("could not delete report {}".format(report_id))
                form.add_error(None, "There was an error deleting your report.")
    else:
        form = forms.ReportAccessForm()
        form.report = report
    context.update({'form': form})
    return render(request, form_template_name, context)
