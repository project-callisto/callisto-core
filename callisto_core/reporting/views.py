import logging

from . import forms, view_partials
from ..delivery import view_partials as delivery_view_partials

logger = logging.getLogger(__name__)


##################
# reporting flow #
##################


class ReportingPrepView(
    view_partials.SubmissionPartial
):
    form_class = forms.PrepForm
    back_url = 'report_view'
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
    form_class = forms.ConfirmationForm
    template_name = 'callisto_core/reporting/reporting_confirmation.html'
    back_url = 'reporting_matching_enter'
    success_url = 'report_view'


#################
# matching flow #
#################


class MatchingPrepView(
    view_partials.SubmissionPartial
):
    form_class = forms.PrepForm
    back_url = 'report_view'
    success_url = 'report_matching_enter'


class MatchingEnterView(
    view_partials.MatchingPartial
):
    form_class = forms.MatchingRequiredForm
    back_url = 'report_matching_prep'
    success_url = 'report_view'


class MatchingWithdrawView(
    delivery_view_partials.ReportActionView,
):

    def _report_action(self):
        self.report.withdraw_from_matching()
