import logging

from django.conf import settings

from . import forms, view_partials
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
        if settings.MATCH_IMMEDIATELY:
            api.MatchingApi.run_matching(
                match_reports_to_check=self.object,
            )
        self._send_confirmation_email(form)
        return super().form_valid(form)
