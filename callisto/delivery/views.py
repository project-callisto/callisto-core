import bugsnag
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import conditional_escape
from ratelimit.decorators import ratelimit

User = get_user_model()

from .forms import SubmitToSchoolForm, SubmitToMatchingFormSet
from .models import Report, MatchReport, EmailNotification
from .report_delivery import PDFFullReport
from .matching import find_matches

from callisto.evaluation.models import EvalRow


@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def submit_to_school(request, report_id):
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
                    PDFFullReport(owner, report, form.decrypted_report).send_report_to_school()
                    report.save()
                except Exception as e:
                    #TODO: real logging
                    bugsnag.notify(e)
                    return render(request, 'submit_to_school.html', {'form': form, 'school_name': settings.SCHOOL_SHORTNAME,
                                                                                  'submit_error': True})

                #record submission in anonymous evaluation data
                try:
                    row = EvalRow()
                    row.anonymise_record(action=EvalRow.SUBMIT, report=report)
                    row.save()
                except Exception as e:
                    #TODO: real logging
                    bugsnag.notify(e)
                    pass

                try:
                    if form.cleaned_data.get('email_confirmation') == "True":
                        notification = EmailNotification.objects.get(name='submit_confirmation')
                        preferred_email = form.cleaned_data.get('email')
                        to_email = set([owner.account.school_email, preferred_email])
                        from_email = '"Callisto Confirmation" <confirmation@{0}>'.format(settings.APP_URL)
                        notification.send(to=to_email, from_email=from_email)
                except Exception as e:
                    #TODO: real logging
                    # report was sent even if confirmation email fails, so don't show an error if so
                    bugsnag.notify(e)

                return render(request, 'submit_to_school_confirmation.html', {'form': form, 'school_name': settings.SCHOOL_SHORTNAME,
                                                                                  'report': report})
        else:
            form = SubmitToSchoolForm(owner, report)
        return render(request, 'submit_to_school.html', {'form': form, 'school_name': settings.SCHOOL_SHORTNAME})
    else:
        return HttpResponseForbidden()

@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def submit_to_matching(request, report_id):
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
                    for perp_form in formset:
                        #enter into matching
                        match_report = MatchReport(report=report)
                        match_report.contact_name = conditional_escape(form.cleaned_data.get('name'))
                        match_report.contact_email = form.cleaned_data.get('email')
                        match_report.contact_phone = conditional_escape(form.cleaned_data.get('phone_number'))
                        match_report.contact_voicemail = conditional_escape(form.cleaned_data.get('voicemail'))
                        match_report.contact_notes = conditional_escape(form.cleaned_data.get('contact_notes'))
                        match_report.identifier = perp_form.cleaned_data.get('perp')
                        match_report.name = conditional_escape(perp_form.cleaned_data.get('perp_name'))
                        match_reports.append(match_report)
                    MatchReport.objects.bulk_create(match_reports)
                    if settings.MATCH_IMMEDIATELY:
                        find_matches()
                except Exception as e:
                    #TODO: real logging
                    bugsnag.notify(e)
                    return render(request, 'submit_to_matching.html', {'form': form, 'formset': formset,
                                                                       'school_name': settings.SCHOOL_SHORTNAME,
                                                                                  'submit_error': True})

                #record matching submission in anonymous evaluation data
                try:
                    row = EvalRow()
                    row.anonymise_record(action=EvalRow.MATCH, report=report)
                    row.save()
                except Exception as e:
                    #TODO: real logging
                    bugsnag.notify(e)
                    pass

                try:
                    if form.cleaned_data.get('email_confirmation') == "True":
                        notification = EmailNotification.objects.get(name='match_confirmation')
                        preferred_email = form.cleaned_data.get('email')
                        to_email = set([owner.account.school_email, preferred_email])
                        from_email = '"Callisto Confirmation" <confirmation@{0}>'.format(settings.APP_URL)
                        notification.send(to=to_email, from_email=from_email)
                except Exception as e:
                    #TODO: real logging
                    # matching was entered even if confirmation email fails, so don't show an error if so
                    bugsnag.notify(e)

                return render(request, 'submit_to_matching_confirmation.html', {'school_name': settings.SCHOOL_SHORTNAME,
                                                                                    'report': report})

        else:
            form = SubmitToSchoolForm(owner, report)
            formset = SubmitToMatchingFormSet()
        return render(request, 'submit_to_matching.html', {'form': form, 'formset': formset,
                                                           'school_name': settings.SCHOOL_SHORTNAME})
    else:
        return HttpResponseForbidden()

def withdraw_from_matching(request, report_id):
    owner = request.user
    report = Report.objects.get(id=report_id)
    if owner == report.owner:
        report.withdraw_from_matching()
        report.save()

        #record match withdrawal in anonymous evaluation data
        try:
            row = EvalRow()
            row.anonymise_record(action=EvalRow.WITHDRAW, report=report)
            row.save()
        except Exception as e:
            #TODO: real logging
            bugsnag.notify(e)
            pass

        return render(request, 'dashboard.html', {'owner': request.user, 'school_name': settings.SCHOOL_SHORTNAME,
                                                        'coordinator_name': settings.COORDINATOR_NAME,
                                                       'coordinator_email': settings.COORDINATOR_EMAIL,
                                                       'match_report_withdrawn': True})
    else:
        return HttpResponseForbidden()
