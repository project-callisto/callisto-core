import json

from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.views import password_reset
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
import bugsnag
from ratelimit.decorators import ratelimit

User = get_user_model()

from .forms import SubmitToSchoolForm, SubmitToMatchingFormSet
from .models import Report, MatchReport, EmailNotification
from account.tokens import student_token_generator
from .report_delivery import send_report_to_school, generate_pdf_report
from .matching import find_matches
from django.utils.html import conditional_escape

from account.forms import SecretKeyForm, SendVerificationEmailForm

@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def view_report(request, report_id):
    owner = request.user
    report = Report.objects.get(id=report_id)
    if owner == report.owner:
        if request.method == 'POST':
            form = SecretKeyForm(request.POST)
            form.report = report
            if form.is_valid():
                return render(request, 'report.html', {'report': json.dumps(json.loads(form.decrypted_report), indent=4)})
        else:
            form = SecretKeyForm()
            form.report = report
        return render(request, 'decrypt_record_for_view.html', {'form': form})
    else:
        return HttpResponseForbidden()

@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def export_report(request, report_id):
    owner = request.user
    report = Report.objects.get(id=report_id)
    if owner == report.owner:
        if request.method == 'POST':
            form = SecretKeyForm(request.POST)
            form.report = report
            if form.is_valid():
                try:
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename="callisto_report.pdf"'
                    pdf = generate_pdf_report(toname=None, user=owner, report=report, decrypted_report=form.decrypted_report, report_id=None)
                    response.write(pdf)
                    return response
                except Exception as e:
                    bugsnag.notify(e)
                    form.add_error(None, "There was an error exporting your report.")
        else:
            form = SecretKeyForm()
            form.report = report
        return render(request, 'decrypt_record_for_view.html', {'form': form})
    else:
        return HttpResponseForbidden()

@ratelimit(group='decrypt', key='user', method=ratelimit.UNSAFE, rate=settings.DECRYPT_THROTTLE_RATE, block=True)
def submit_to_school(request, report_id):
    owner = request.user
    report = Report.objects.get(id=report_id)
    if owner == report.owner:
        if not owner.account.is_verified:
            VerificationForm = type('SendVerificationForm', (SendVerificationEmailForm,),
                                    {"user" : request.user})

            #using django's password reset functionality to send this email
            return password_reset(request, template_name='submit_to_school.html',
                                    email_template_name='student_verification_email_plain.html',
                                    html_email_template_name='student_verification_email.html',
                                    subject_template_name='student_verification_email_subject.txt',
                                    post_reset_redirect=reverse('student_verification_sent', args=["submit", report_id]), #TODO: ajax?
                                    password_reset_form=VerificationForm,
                                    token_generator=student_token_generator,
                                    extra_context = {'school_name': settings.SCHOOL_SHORTNAME})
        else:
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
                        report.submitted_to_school = timezone.now()
                        send_report_to_school(owner, report, form.decrypted_report)
                        report.save()
                    except Exception as e:
                        #TODO: real logging
                        bugsnag.notify(e)
                        return render(request, 'submit_to_school.html', {'form': form, 'school_name': settings.SCHOOL_SHORTNAME,
                                                                                      'submit_error': True})
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
        if not owner.account.is_verified:
            VerificationForm = type('SendVerificationForm', (SendVerificationEmailForm,),
                                    {"user" : request.user})

            #using django's password reset functionality to send this email
            return password_reset(request, template_name='submit_to_matching.html',
                                    email_template_name='student_verification_email_plain.html',
                                    html_email_template_name='student_verification_email.html',
                                    subject_template_name='student_verification_email_subject.txt',
                                    post_reset_redirect=reverse('student_verification_sent', args=["match", report_id]), #TODO: ajax?
                                    password_reset_form=VerificationForm,
                                    token_generator=student_token_generator,
                                    extra_context = {'school_name': settings.SCHOOL_SHORTNAME})
        else:
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
                    try:
                        if form.cleaned_data.get('email_confirmation'):
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
        return render(request, 'dashboard.html', {'owner': request.user, 'school_name': settings.SCHOOL_SHORTNAME,
                                                        'coordinator_name': settings.COORDINATOR_NAME,
                                                       'coordinator_email': settings.COORDINATOR_EMAIL,
                                                       'match_report_withdrawn': True})
    else:
        return HttpResponseForbidden()

def ratelimit(request, exception):
    bugsnag.notify(exception)
    return render(request, 'ratelimit.html')