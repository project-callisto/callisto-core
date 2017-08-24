import logging

from django.conf import settings

from . import forms, view_partials
from ..delivery import (
    models as delivery_models, view_partials as delivery_view_partials,
)
from ..utils import api

logger = logging.getLogger(__name__)


##################
# reporting flow #
##################


class ReportingPrepView(
    view_partials.PrepPartial
):
    form_class = forms.PrepForm
    success_url = 'reporting_matching_enter'


class ReportingMatchingView(
    view_partials.MatchingPartial
):
    form_class = forms.MatchingOptionalForm
    template_name = 'callisto_core/reporting/reporting_matching.html'
    back_url = 'reporting_prep'
    success_url = 'reporting_confirmation'


class ReportingConfirmationView(
    view_partials.ConfirmationPartial
):
    template_name = 'callisto_core/reporting/reporting_confirmation.html'
    back_url = 'reporting_matching_enter'


#################
# matching flow #
#################


class MatchingPrepView(
    view_partials.PrepPartial
):
    form_class = forms.PrepForm
    back_url = 'report_view'
    success_url = 'matching_enter'


class MatchingEnterView(
    view_partials.MatchingPartial
):
    form_class = forms.MatchingRequiredForm
    back_url = 'matching_prep'
    success_url = 'matching_confirmation'


class MatchingConfirmationView(
    view_partials.ConfirmationPartial
):
    template_name = 'callisto_core/reporting/reporting_confirmation.html'


class MatchingWithdrawView(
    delivery_view_partials.ReportActionView,
):

    def _report_action(self):
        self.report.withdraw_from_matching()


# TEMP


class ReportingView(
    view_partials.BaseReportingView,
):

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
        return output
