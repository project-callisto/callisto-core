import json
import logging

from django.conf import settings

from . import forms, report_delivery, view_partials
from ..delivery import (
    models as delivery_models, view_partials as delivery_view_partials,
)
from ..utils import api

logger = logging.getLogger(__name__)


class MatchingWithdrawView(
    delivery_view_partials.ReportActionView,
):

    def _report_action(self):
        # TODO: self.action.withdraw()
        self.report.withdraw_from_matching()


class ReportingView(
    view_partials.BaseReportingView,
):
    form_class = forms.ReportingForm
    email_confirmation_name = 'submit_confirmation'

    def form_valid(self, form):
        output = super().form_valid(form)
        sent_full_report = delivery_models.SentFullReport.objects.create(
            report=self.report,
            to_address=settings.COORDINATOR_EMAIL,
        )
        api.NotificationApi.send_report_to_authority(
            sent_full_report,
            form.decrypted_report,
            self.site_id,
        )
        self._send_confirmation_email(form)
        return output


class MatchingView(
    view_partials.BaseReportingView,
):
    form_class = forms.SubmitToMatchingForm
    email_confirmation_name = 'match_confirmation'

    def form_valid(self, form):
        output = super().form_valid(form)

        matches_for_immediate_processing = []
        for perp_form in form:
            match_report = delivery_models.MatchReport(report=self.report)

            perp_identifier = perp_form.cleaned_data.get('perp')
            match_report.contact_email = form.cleaned_data.get('email')
            match_report_content = report_delivery.MatchReportContent(
                identifier=perp_identifier,
                perp_name=perp_form.cleaned_data.get('perp_name'),
                contact_name=form.cleaned_data.get('name'),
                email=match_report.contact_email,
                phone=form.cleaned_data.get('phone_number'),
                voicemail=form.cleaned_data.get('voicemail'),
                notes=form.cleaned_data.get('contact_notes'),
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
            api.MatchingApi.run_matching(
                match_reports_to_check=matches_for_immediate_processing)

        return output
