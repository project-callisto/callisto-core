import json
import logging

from ratelimit.decorators import ratelimit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils.html import conditional_escape

from callisto.evaluation.models import EvalRow

from .forms import SubmitToMatchingFormSet, SubmitToSchoolForm
from .matching import run_matching
from .models import EmailNotification, MatchReport, Report
from .report_delivery import MatchReportContent, PDFFullReport, PDFMatchReport

User = get_user_model()
logger = logging.getLogger(__name__)


def _send_user_notification(form, notification_name):
    if form.cleaned_data.get('email_confirmation') == "True":
        notification = EmailNotification.objects.get(name=notification_name)
        preferred_email = form.cleaned_data.get('email')
        to_email = preferred_email
        from_email = '"Callisto Confirmation" <confirmation@{0}>'.format(settings.APP_URL)
        notification.send(to=[to_email], from_email=from_email)


@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def submit_to_school(request, report_id, form_template_name="submit_to_school.html",
                     confirmation_template_name="submit_to_school_confirmation.html",
                     report_class=PDFFullReport):
    owner = request.user
    report = Report.objects.get(id=report_id)
    if owner == report.owner:
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
                    report_class(report=report, decrypted_report=form.decrypted_report).send_report_to_school()
                    report.save()
                except Exception:
                    logger.exception("couldn't submit report for report {}".format(report_id))
                    return render(request, form_template_name, {'form': form, 'school_name': settings.SCHOOL_SHORTNAME,
                                                                                  'submit_error': True})

                #record submission in anonymous evaluation data
                try:
                    row = EvalRow()
                    row.anonymise_record(action=EvalRow.SUBMIT, report=report)
                    row.save()
                except Exception:
                    logger.exception("couldn't save evaluation row on submission")
                    pass

                try:
                    _send_user_notification(form, 'submit_confirmation')
                except Exception:
                    # report was sent even if confirmation email fails, so don't show an error if so
                    logger.exception("couldn't send confirmation to user on submission")

                return render(request, confirmation_template_name, {'form': form, 'school_name': settings.SCHOOL_SHORTNAME,
                                                                                  'report': report})
        else:
            form = SubmitToSchoolForm(owner, report)
        return render(request, form_template_name, {'form': form, 'school_name': settings.SCHOOL_SHORTNAME})
    else:
        logger.warning("illegal submit attempt on record {} by user {}".format(report_id, owner.id))
        return HttpResponseForbidden()


@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def submit_to_matching(request, report_id, form_template_name="submit_to_matching.html",
                       confirmation_template_name="submit_to_matching_confirmation.html",
                       report_class=PDFMatchReport):
    owner = request.user
    report = Report.objects.get(id=report_id)
    if owner == report.owner:
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
                    return render(request, form_template_name, {'form': form, 'formset': formset,
                                                                'school_name': settings.SCHOOL_SHORTNAME,
                                                                'submit_error': True})

                #record matching submission in anonymous evaluation data
                try:
                    row = EvalRow()
                    row.anonymise_record(action=EvalRow.MATCH, report=report)
                    row.save()
                except Exception:
                    logger.exception("couldn't save evaluation row on match submission")
                    pass

                try:
                    _send_user_notification(form, 'match_confirmation')
                except Exception:
                    # matching was entered even if confirmation email fails, so don't show an error if so
                    logger.exception("couldn't send confirmation to user on match submission")

                return render(request, confirmation_template_name, {'school_name': settings.SCHOOL_SHORTNAME,
                                                                                    'report': report})

        else:
            form = SubmitToSchoolForm(owner, report)
            formset = SubmitToMatchingFormSet()
        return render(request, form_template_name, {'form': form, 'formset': formset,
                                                           'school_name': settings.SCHOOL_SHORTNAME})
    else:
        logger.warning("illegal matching attempt on record {} by user {}".format(report_id, owner.id))
        return HttpResponseForbidden()


def withdraw_from_matching(request, report_id, template_name):
    owner = request.user
    report = Report.objects.get(id=report_id)
    if owner == report.owner:
        report.withdraw_from_matching()
        report.save()

        # record match withdrawal in anonymous evaluation data
        try:
            row = EvalRow()
            row.anonymise_record(action=EvalRow.WITHDRAW, report=report)
            row.save()
        except Exception:
            logger.exception("couldn't save evaluation row on match withdrawal")
            pass

        return render(request, template_name, {'owner': request.user, 'school_name': settings.SCHOOL_SHORTNAME,
                                                        'coordinator_name': settings.COORDINATOR_NAME,
                                                       'coordinator_email': settings.COORDINATOR_EMAIL,
                                                       'match_report_withdrawn': True})
    else:
        logger.warning("illegal matching withdrawal attempt on record {} by user {}".format(report_id, owner.id))
        return HttpResponseForbidden()
