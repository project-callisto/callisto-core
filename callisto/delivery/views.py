import json
import logging
from functools import wraps

from ratelimit.decorators import ratelimit
from wizard_builder.models import PageBase

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.http import (
    HttpResponse, HttpResponseForbidden, HttpResponseNotFound,
    HttpResponseServerError,
)
from django.shortcuts import render
from django.utils.decorators import available_attrs
from django.utils.html import conditional_escape

from callisto.evaluation.models import EvalRow
from callisto.notification.models import EmailNotification

from .forms import SecretKeyForm, SubmitToMatchingFormSet, SubmitToSchoolForm
from .matching import run_matching
from .models import MatchReport, Report
from .report_delivery import MatchReportContent, PDFFullReport, PDFMatchReport

User = get_user_model()
logger = logging.getLogger(__name__)


def check_owner(action_name, report_id_arg='report_id'):
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            owner = request.user
            # kludgy assumption that report_id will be first arg after request
            id_to_fetch = kwargs.get(report_id_arg) or args[0]
            try:
                report = Report.objects.get(id=id_to_fetch)
                if owner == report.owner:
                    return view_func(request, *args, **kwargs)
                else:
                    logger.warning("illegal {} attempt on record {} by user {}".format(action_name,
                                                                                       id_to_fetch, owner.id))
                    return HttpResponseForbidden() if settings.DEBUG else HttpResponseNotFound()
            except ObjectDoesNotExist:
                return HttpResponseNotFound()
        return _wrapped_view
    return decorator


def new_record_form_view(request, wizard, step=None, url_name="record_form"):
    if PageBase.objects.count() > 0:
        return wizard.wizard_factory().as_view(url_name=url_name)(request, step=step)
    else:
        logger.error("no pages in record form")
        return HttpResponseServerError()


@check_owner('edit', 'edit_id')
@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def edit_record_form_view(request, edit_id, wizard, step=None, url_name="edit_report"):
    report = Report.objects.get(id=edit_id)
    if PageBase.objects.count() > 0:
        return wizard.wizard_factory(object_to_edit=report).as_view(url_name=url_name)(request, step=step)
    else:
        logger.error("no pages in record form")
        return HttpResponseServerError()


def _send_user_notification(request, form, notification_name):
    if form.cleaned_data.get('email_confirmation') == "True":
        site = get_current_site(request)
        notification = EmailNotification.objects.on_site(site.id).get(name=notification_name)
        preferred_email = form.cleaned_data.get('email')
        to_email = preferred_email
        from_email = '"Callisto Confirmation" <confirmation@{0}>'.format(settings.APP_URL)
        notification.send(to=[to_email], from_email=from_email)


@check_owner('submit')
@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def submit_to_school(request, report_id, form_template_name="submit_to_school.html",
                     confirmation_template_name="submit_to_school_confirmation.html",
                     report_class=PDFFullReport, extra_context=None):
    owner = request.user
    report = Report.objects.get(id=report_id)
    context = {'owner': owner, 'report': report}
    context.update(extra_context or {})

    if request.method == 'POST':
        form = SubmitToSchoolForm(owner, report, request.POST)
        form.report = report
        if form.is_valid():
            try:
                report.contact_name = conditional_escape(form.cleaned_data.get('name'))
                report.contact_email = form.cleaned_data.get('email')
                report.contact_phone = conditional_escape(form.cleaned_data.get('phone_number'))
                report.contact_voicemail = conditional_escape(form.cleaned_data.get('voicemail'))
                report.contact_notes = conditional_escape(form.cleaned_data.get('contact_notes'))
                report_class(report=report, decrypted_report=form.decrypted_report).send_report_to_school(request)
                report.save()
            except Exception:
                logger.exception("couldn't submit report for report {}".format(report_id))
                context.update({'form': form, 'submit_error': True})
                return render(request, form_template_name, context)

            # record submission in anonymous evaluation data
            EvalRow.store_eval_row(action=EvalRow.SUBMIT, report=report)

            try:
                _send_user_notification(request, form, 'submit_confirmation')
            except Exception:
                # report was sent even if confirmation email fails, so don't show an error if so
                logger.exception("couldn't send confirmation to user on submission")

            context.update({'form': form})
            return render(request, confirmation_template_name, context)
    else:
        form = SubmitToSchoolForm(owner, report)
    context.update({'form': form})
    return render(request, form_template_name, context)


@check_owner('matching')
@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def submit_to_matching(request, report_id, form_template_name="submit_to_matching.html",
                       confirmation_template_name="submit_to_matching_confirmation.html",
                       report_class=PDFMatchReport, extra_context=None):
    owner = request.user
    report = Report.objects.get(id=report_id)
    context = {'owner': owner, 'report': report}
    context.update(extra_context or {})

    if request.method == 'POST':
        form = SubmitToSchoolForm(owner, report, request.POST)
        formset = SubmitToMatchingFormSet(request.POST)
        form.report = report
        if form.is_valid() and formset.is_valid():
            try:
                match_reports = []
                identifiers = []
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
                        identifiers.append(perp_identifier)
                    else:
                        match_report.identifier = perp_identifier
                    match_reports.append(match_report)
                MatchReport.objects.bulk_create(match_reports)
                if settings.MATCH_IMMEDIATELY:
                    run_matching(identifiers=identifiers, report_class=report_class)
            except Exception:
                logger.exception("couldn't submit match report for report {}".format(report_id))
                context.update({'form': form, 'formset': formset, 'submit_error': True})
                return render(request, form_template_name, context)

            # record matching submission in anonymous evaluation data
            EvalRow.store_eval_row(action=EvalRow.MATCH, report=report, match_identifier=perp_identifier)

            try:
                _send_user_notification(request, form, 'match_confirmation')
            except Exception:
                # matching was entered even if confirmation email fails, so don't show an error if so
                logger.exception("couldn't send confirmation to user on match submission")

            return render(request, confirmation_template_name, context)

    else:
        form = SubmitToSchoolForm(owner, report)
        formset = SubmitToMatchingFormSet()
    context.update({'form': form, 'formset': formset})
    return render(request, form_template_name, context)


@check_owner('matching withdrawal')
def withdraw_from_matching(request, report_id, template_name, extra_context=None):
    report = Report.objects.get(id=report_id)
    context = {'owner': request.user}
    context.update(extra_context or {})

    report.withdraw_from_matching()
    report.save()
    # record match withdrawal in anonymous evaluation data
    EvalRow.store_eval_row(action=EvalRow.WITHDRAW, report=report)

    context.update({'match_report_withdrawn': True})
    return render(request, template_name, context)


@check_owner('export')
@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def export_as_pdf(request, report_id, force_download=True, filename='report.pdf', report_class=PDFFullReport,
                  template_name='export_report.html', extra_context=None):
    report = Report.objects.get(id=report_id)
    context = {'owner': request.user, 'report': report}
    context.update(extra_context or {})
    if request.method == 'POST':
        form = SecretKeyForm(request.POST)
        form.report = report
        if form.is_valid():
            EvalRow.store_eval_row(action=EvalRow.VIEW, report=report)
            try:
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = '{}; filename="{}"'\
                    .format('attachment' if force_download else 'inline', filename)
                pdf = report_class(report=report, decrypted_report=form.decrypted_report)\
                    .generate_pdf_report(recipient=None, report_id=None)
                response.write(pdf)
                return response
            except Exception:
                logger.exception("could not export report {}".format(report_id))
                form.add_error(None, "There was an error exporting your report.")
    else:
        form = SecretKeyForm()
        form.report = report
    context.update({'form': form})
    return render(request, template_name, context)


@check_owner('delete')
@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def delete_report(request, report_id, form_template_name='delete_report.html',
                  confirmation_template='delete_report.html', extra_context=None):
    report = Report.objects.get(id=report_id)
    context = {'owner': request.user}
    context.update(extra_context or {})
    if request.method == 'POST':
        form = SecretKeyForm(request.POST)
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
        form = SecretKeyForm()
        form.report = report
    context.update({'form': form})
    return render(request, form_template_name, context)
