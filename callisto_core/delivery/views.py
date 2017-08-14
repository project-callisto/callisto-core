import json
import logging

from ratelimit.decorators import ratelimit

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

    def set_key(self, key):
        self.view.request.session['secret_key'] = key

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
    def report(self):
        return self.object

    @property
    def storage(self):
        return self.storage_helper(self)

    def form_valid(self, form):
        self.storage.set_key(form.data['key'])
        return super().form_valid(form)


class ReportCreateView(
    ReportBaseView,
    views.edit.CreateView,
):
    form_class = forms.ReportCreateForm

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
):
    access_form_class = forms.ReportAccessForm
    invalid_access_message = 'Invalid access request at url {}'

    def _log_invalid_access(self):
        logger.info(self.invalid_access_message.format(
            self.request.get_full_path()))

    def get_context_data(self, **kwargs):
        if self.storage.secret_key:
            return super().get_context_data(**kwargs)
        else:
            self._log_invalid_access()
            kwargs['form'] = self.access_form_class
            return super().get_context_data(**kwargs)


@ratelimit(
    group='decrypt',
    key='user',
    method=ratelimit.UNSAFE,
    rate=settings.DECRYPT_THROTTLE_RATE,
    block=True,
)
def submit_report_to_authority(
    request,
    report_id,
    form_template_name="submit_report_to_authority.html",
    confirmation_template_name="submit_report_to_authority_confirmation.html",
    extra_context=None,
):
    report = Report.objects.get(id=report_id)
    owner = report.owner
    site = get_current_site(request)
    context = {'owner': owner, 'report': report, **extra_context}

    if request.method == 'POST':
        form = forms.SubmitReportToAuthorityForm(report.owner, report, request.POST)
        form.report = report
        if form.is_valid():
            try:
                report.contact_name = conditional_escape(form.cleaned_data.get('name'))
                report.contact_email = form.cleaned_data.get('email')
                report.contact_phone = conditional_escape(form.cleaned_data.get('phone_number'))
                report.contact_voicemail = conditional_escape(form.cleaned_data.get('voicemail'))
                report.contact_notes = conditional_escape(form.cleaned_data.get('contact_notes'))
                sent_full_report = SentFullReport.objects.create(report=report, to_address=settings.COORDINATOR_EMAIL)
                NotificationApi.send_report_to_authority(sent_full_report, form.decrypted_report, site.id)
                report.save()
            except Exception:
                logger.exception("couldn't submit report for report {}".format(report_id))
                context.update({'form': form, 'submit_error': True})
                return render(request, form_template_name, context)

            # record submission in anonymous evaluation data
            EvalRow.store_eval_row(action=EvalRow.SUBMIT, report=report)

            if form.cleaned_data.get('email_confirmation') == "True":
                try:
                    NotificationApi.send_user_notification(form, 'submit_confirmation', site.id)
                except Exception:
                    # report was sent even if confirmation email fails, so don't show an error if so
                    logger.exception("couldn't send confirmation to user on submission")

            context.update({'form': form})
            return render(request, confirmation_template_name, context)
    else:
        form = forms.SubmitReportToAuthorityForm(report.owner, report)
    context.update({'form': form})
    return render(request, form_template_name, context)


@ratelimit(
    group='decrypt',
    key='user',
    method=ratelimit.UNSAFE,
    rate=settings.DECRYPT_THROTTLE_RATE,
    block=True,
)
def submit_to_matching(
    request,
    report_id,
    form_template_name="submit_to_matching.html",
    confirmation_template_name="submit_to_matching_confirmation.html",
    extra_context=None,
):
    report = Report.objects.get(id=report_id)
    owner = report.owner
    site = get_current_site(request)
    context = {'owner': owner, 'report': report, **extra_context}

    if request.method == 'POST':
        form = forms.SubmitReportToAuthorityForm(report.owner, report, request.POST)
        formset = forms.SubmitToMatchingFormSet(request.POST)
        form.report = report
        if form.is_valid() and formset.is_valid():
            try:
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

                if settings.MATCH_IMMEDIATELY:
                    MatchingApi.run_matching(match_reports_to_check=matches_for_immediate_processing)

            except Exception:
                logger.exception("couldn't submit match report for report {}".format(report_id))
                context.update({'form': form, 'formset': formset, 'submit_error': True})
                return render(request, form_template_name, context)

            if form.cleaned_data.get('email_confirmation') == "True":
                try:
                    NotificationApi.send_user_notification(form, 'match_confirmation', site.id)
                except Exception:
                    # matching was entered even if confirmation email fails, so don't show an error if so
                    logger.exception("couldn't send confirmation to user on match submission")

            return render(request, confirmation_template_name, context)

    else:
        form = forms.SubmitReportToAuthorityForm(report.owner, report)
        formset = forms.SubmitToMatchingFormSet()
    context.update({'form': form, 'formset': formset})
    return render(request, form_template_name, context)


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


@ratelimit(
    group='decrypt',
    key='user',
    method=ratelimit.UNSAFE,
    rate=settings.DECRYPT_THROTTLE_RATE,
    block=True,
)
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


@ratelimit(
    group='decrypt',
    key='user',
    method=ratelimit.UNSAFE,
    rate=settings.DECRYPT_THROTTLE_RATE,
    block=True,
)
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
