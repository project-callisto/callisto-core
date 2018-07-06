'''

View partials provide all the callisto-core front-end functionality.
Subclass these partials with your own views if you are implementing
callisto-core. Many of the view partials only provide a subset of the
functionality required for a full HTML view.

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/

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
from django.contrib.auth.views import PasswordResetView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic.edit import FormView

from callisto_core.accounts import (
    forms as account_forms, tokens as account_tokens,
)
from callisto_core.delivery import view_partials as delivery_partials
from callisto_core.utils.api import MatchingApi, NotificationApi, TenantApi

from . import forms, validators, view_helpers


class _SubmissionPartial(
    view_helpers.ReportingSuccessUrlMixin,
    delivery_partials._ReportUpdatePartial,
):
    back_url = None

    @property
    def all_user_emails(self):
        return [
            self.report.owner.email,
            self.report.owner.account.school_email,
            self.report.contact_email,
        ]

    @property
    def in_demo_mode(self):
        return TenantApi.site_settings(
            'DEMO_MODE', request=self.request, cast=bool)

    @property
    def coordinator_emails(self):
        return TenantApi.site_settings(
            'COORDINATOR_EMAIL', request=self.request)

    @property
    def coordinator_public_key(self):
        return TenantApi.site_settings(
            'COORDINATOR_PUBLIC_KEY', request=self.request)

    @property
    def school_name(self):
        return TenantApi.site_settings(
            'SCHOOL_SHORTNAME', request=self.request)

    @property
    def school_email_domain(self):
        return TenantApi.site_settings(
            'SCHOOL_EMAIL_DOMAIN', request=self.request)


class CallistoPasswordResetView(PasswordResetView, FormView):
    '''
    Workaround for bug in PasswordResetView's form_valid() function
    where it calls get_current_site() from its save() method. To
    workaround this we overload PasswordResetView's form_valid()
    method and set save()'s 'domain_override' option in order to
    bypass calls to get_current_site().
    '''

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'domain_override': self.request.site.domain,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        form.save(**opts)

        # Do not call super() for our parents. They will all call save()
        # wrong way again and cause us much sadness (broken notifications).
        # Instead, we must call "HttpResponseRedirect" as per the parent
        # Mixin class (see: django/views/generic/edit.py).
        return HttpResponseRedirect(self.get_success_url())


class SchoolEmailFormPartial(
    _SubmissionPartial,
    CallistoPasswordResetView,
):
    form_class = account_forms.ReportingVerificationEmailForm
    token_generator = account_tokens.StudentVerificationTokenGenerator()
    # success_url is used for inputting a valid school email address
    success_url = None
    # next_url is used for having your account already verified,
    # and inputting a correct account verification token
    next_url = None
    EVAL_ACTION_TYPE = 'SCHOOL_EMAIL_ENTRY'

    @property
    def student_confirmation_url(self):
        uidb64 = urlsafe_base64_encode(
            force_bytes(self.request.user.pk)).decode("utf-8")
        token = self.token_generator.make_token(self.request.user)
        return reverse(
            self.request.resolver_match.view_name,
            kwargs={
                'uuid': self.report.uuid,
                'uidb64': uidb64,
                'token': token,
            },
        )

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.account.is_verified:
            return self._redirect_to_next()
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(self.success_url)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'school_email_domain': self.school_email_domain,
        })
        return kwargs

    def form_valid(self, form):
        self._update_email(form)
        self._send_mail(form)
        return super().form_valid(form)

    def _update_email(self, form):
        self.request.user.account.school_email = form.cleaned_data.get('email')
        self.request.user.account.save()

    def _send_mail(self, form):
        NotificationApi.send_with_kwargs(
            site_id=self.request.user.account.site_id,
            to_addresses=[form.cleaned_data.get('email')],
            email_subject='Verify your student email',
            email_name='student_verification_email',
            redirect_url=self.student_confirmation_url,
            email_template_name=self.email_template_name,
            user=self.request.user,
        )

    def _redirect_to_next(self):
        next_url = reverse(
            self.next_url,
            kwargs={'uuid': self.report.uuid},
        )
        return redirect(next_url)


class SchoolEmailConfirmationPartial(
    SchoolEmailFormPartial,
):
    EVAL_ACTION_TYPE = 'SCHOOL_EMAIL_CONFIRMATION'

    def verify_email(self):
        self.request.user.account.is_verified = True
        self.request.user.account.save()

    def dispatch(self, request, token=None, uidb64=None, *args, **kwargs):
        if self.token_generator.check_token(self.request.user, token):
            self.verify_email()
            return self._redirect_to_next()
        else:
            return super().dispatch(self.request, *args, **kwargs)


class PrepPartial(
    _SubmissionPartial,
):
    form_class = forms.PrepForm
    EVAL_ACTION_TYPE = 'CONTACT_INFO_PREPERATION'


class ResubmitPrepPartial(
    PrepPartial,
):
    EVAL_ACTION_TYPE = 'RESUBMIT_CONTACT_INFO_PREPERATION'


class _ReportSubclassPartial(
    _SubmissionPartial,
):

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': None})  # TODO: remove
        return kwargs


class _MatchingPartial(
    _ReportSubclassPartial,
):
    matching_validator_class = validators.Validators

    def get_matching_validators(self, *args, **kwargs):
        return self.matching_validator_class()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'matching_validators': self.get_matching_validators()})
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        identifier = form.cleaned_data.get('identifier')
        matches = self._get_matches(identifier)

        self._notify_owner_of_submission(identifier)
        if matches:
            self._notify_authority_of_matches(matches, identifier)
            self._notify_owners_of_matches(matches)
            self._slack_match_notification()
            self._match_confirmation_email_to_callisto(matches)

        return response

    def _get_matches(self, identifier):
        return MatchingApi.find_matches(identifier)

    def _slack_match_notification(self):
        if not self.in_demo_mode:
            NotificationApi.slack_notification(
                msg='New Callisto Matches (details will be sent via email)',
                type='match_confirmation',
            )

    def _match_confirmation_email_to_callisto(self, matches):
        if not self.in_demo_mode:
            NotificationApi.send_with_kwargs(
                site_id=self.site_id,  # required in general
                email_template_name=self.admin_email_template_name,  # the email template
                to_addresses=NotificationApi.ALERT_LIST,  # addresses to send to
                matches=matches,  # used in the email body
                email_subject='New Callisto Matches',  # rendered as the email subject
                email_name='match_confirmation_callisto_team',  # used in test assertions
            )

    def _notify_owner_of_submission(self, identifier):
        if identifier:
            NotificationApi.send_confirmation(
                email_type='match_confirmation',
                to_addresses=[self.report.contact_email],
                site_id=self.site_id,
            )

    def _notify_authority_of_matches(self, matches, identifier):
        NotificationApi.send_matching_report_to_authority(
            matches=matches,
            identifier=identifier,
            to_addresses=self.coordinator_emails,
            public_key=self.coordinator_public_key,
        )

    def _notify_owners_of_matches(self, matches):
        for match in matches:
            NotificationApi.send_match_notification(
                match_report=match,
            )


class OptionalMatchingPartial(
    _MatchingPartial,
):
    EVAL_ACTION_TYPE = 'ENTER_MATCHING_OPTIONAL'
    form_class = forms.MatchingOptionalForm


class RequiredMatchingPartial(
    _MatchingPartial,
):
    EVAL_ACTION_TYPE = 'ENTER_MATCHING_REQUIRED'
    form_class = forms.MatchingRequiredForm


class ConfirmationPartial(
    _ReportSubclassPartial,
):
    form_class = forms.ConfirmationForm
    EVAL_ACTION_TYPE = 'DIRECT_REPORTING_FINAL_CONFIRMATION'
    SLACK_ALERT_TEXT = 'New Callisto Report at {school_name} (details will be sent via email)'

    def form_valid(self, form):
        output = super().form_valid(form)
        self._save_to_address(form)
        self._send_report_alerts()
        return output

    def _send_report_to_authority(self, report):
        kwargs = {
            'sent_report': report,
            'report_data': self.storage.cleaned_form_data,
            'site_id': self.site_id,
            'to_addresses': [self.coordinator_emails],
            'public_key': self.coordinator_public_key,
        }
        if self.in_demo_mode:
            kwargs['DEMO_MODE'] = True
            kwargs['to_addresses'] += self.all_user_emails
        NotificationApi.send_report_to_authority(**kwargs)

    def _send_confirmation_email(self):
        kwargs = {
            'email_type': 'submit_confirmation',
            'to_addresses': [self.report.contact_email],
            'site_id': self.site_id,
        }
        if self.in_demo_mode:
            kwargs['DEMO_MODE'] = True
            kwargs['to_addresses'] += self.all_user_emails
        NotificationApi.send_confirmation(**kwargs)

    def _send_confirmation_email_to_callisto(self):
        if not self.in_demo_mode:
            NotificationApi.send_with_kwargs(
                site_id=self.site_id,  # required in general
                email_template_name=self.admin_email_template_name,  # the email template
                to_addresses=NotificationApi.ALERT_LIST,  # addresses to send to
                report=self.report,  # used in the email body
                email_subject='New Callisto Report',  # rendered as the email subject
            )

    def _send_confirmation_slack_notification(self):
        if not self.in_demo_mode:
            NotificationApi.slack_notification(
                msg=self.SLACK_ALERT_TEXT.format(school_name=self.school_name),
                type='submit_confirmation',
            )

    def _save_to_address(self, form):
        sent_report = form.instance
        sent_report.to_address = self.coordinator_emails
        sent_report.save()

    def _send_report_alerts(self):
        for sent_full_report in self.report.sentfullreport_set.all():
            self._send_report_to_authority(sent_full_report)
        self._send_confirmation_email()
        self._send_confirmation_email_to_callisto()
        self._send_confirmation_slack_notification()


class ResubmitConfirmationPartial(
    ConfirmationPartial,
):
    form_class = forms.ConfirmedConfirmationForm
    EVAL_ACTION_TYPE = 'RESUBMIT_FINAL_CONFIRMATION'
    SLACK_ALERT_TEXT = 'Resubmitted Callisto Report at {school_name} (details will be sent via email)'


class MatchingWithdrawPartial(
    view_helpers.ReportingSuccessUrlMixin,
    delivery_partials._ReportActionPartial,
):
    EVAL_ACTION_TYPE = 'MATCHING_WITHDRAW'

    def view_action(self):
        self.report.withdraw_from_matching()
