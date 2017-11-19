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
from callisto_core.delivery import view_partials as delivery_partials
from callisto_core.utils.api import MatchingApi, NotificationApi, TenantApi

from django.conf import settings

from . import forms, validators, view_helpers


class SubmissionPartial(
    view_helpers.ReportingSuccessUrlMixin,
    delivery_partials.ReportUpdatePartial,
):
    back_url = None

    @property
    def coordinator_emails(self):
        return TenantApi.site_settings(
            'COORDINATOR_EMAIL', request=self.request)


class PrepPartial(
    SubmissionPartial,
):
    form_class = forms.PrepForm


class ReportSubclassPartial(
    SubmissionPartial,
):

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': None})  # TODO: remove
        return kwargs


class MatchingPartial(
    ReportSubclassPartial,
):
    matching_validator_class = validators.Validators

    def get_matching_validators(self, *args, **kwargs):
        return self.matching_validator_class()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'matching_validators': self.get_matching_validators()})
        return kwargs

    def form_valid(self, form):
        output = super().form_valid(form)
        if form.data.get('identifier'):
            self._send_match_email()
            self._find_matches(form)
        return output

    def _find_matches(self, form):
        MatchingApi.find_matches(
            match_report=form.instance,
            identifier=form.data.get('identifier'),
            to_coordinators=self.coordinator_emails,
        )

    def _send_match_email(self):
        NotificationApi.send_confirmation(
            email_type='match_confirmation',
            to_addresses=[self.report.contact_email],
            site_id=self.site_id,
        )


class OptionalMatchingPartial(
    MatchingPartial,
):
    form_class = forms.MatchingOptionalForm


class RequiredMatchingPartial(
    MatchingPartial,
):
    form_class = forms.MatchingRequiredForm


class ConfirmationPartial(
    ReportSubclassPartial,
):
    form_class = forms.ConfirmationForm

    def _send_report_to_authority(self, report):
        NotificationApi.send_report_to_authority(
            sent_report=report,
            report_data=self.storage.cleaned_form_data,
            site_id=self.site_id,
            to_addresses=self.coordinator_emails,
        )

    def _send_confirmation_email(self):
        NotificationApi.send_confirmation(
            email_type='submit_confirmation',
            to_addresses=[self.report.contact_email],
            site_id=self.site_id,
        )

    def _send_report_emails(self):
        for sent_full_report in self.report.sentfullreport_set.all():
            self._send_report_to_authority(sent_full_report)
        self._send_confirmation_email()

    def form_valid(self, form):
        output = super().form_valid(form)
        self._send_report_emails()
        return output


class MatchingWithdrawPartial(
    view_helpers.ReportingSuccessUrlMixin,
    delivery_partials.ReportActionPartial,
):

    def view_action(self):
        self.report.withdraw_from_matching()
