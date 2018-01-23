'''

Views specific to callisto-core, if you are implementing callisto-core
you SHOULD NOT be importing these views. Import from view_partials instead.
All of the classes in this file should represent one of more HTML view.

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/

views should define:
    - templates

'''
from . import view_partials

##################
# reporting flow #
##################


class ReportingSchoolEmailFormView(
    view_partials.SchoolEmailFormPartial,
):
    template_name = 'callisto_core/reporting/submission.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'
    email_template_name = 'callisto_core/reporting/student_verification_email.html'


class ReportingSchoolEmailConfirmationView(
    view_partials.SchoolEmailConfirmationPartial,
):
    template_name = 'callisto_core/delivery/form.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'


class ReportingPrepView(
    view_partials.PrepPartial
):
    template_name = 'callisto_core/reporting/submission.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'


class ReportingMatchingView(
    view_partials.OptionalMatchingPartial
):
    template_name = 'callisto_core/reporting/submission.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'
    admin_email_template_name = 'callisto_core/accounts/match_confirmation_callisto_team.html'


class ReportingConfirmationView(
    view_partials.ConfirmationPartial
):
    template_name = 'callisto_core/reporting/submission_confirm.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'
    admin_email_template_name = 'callisto_core/accounts/submit_confirmation_callisto_team.html'


#################
# matching flow #
#################


class MatchingSchoolEmailFormView(
    view_partials.SchoolEmailFormPartial,
):
    template_name = 'callisto_core/reporting/submission.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'
    email_template_name = 'callisto_core/reporting/student_verification_email.html'


class MatchingSchoolEmailConfirmationView(
    view_partials.SchoolEmailConfirmationPartial,
):
    template_name = 'callisto_core/delivery/form_redirect.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'


class MatchingPrepView(
    view_partials.PrepPartial
):
    template_name = 'callisto_core/reporting/submission.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'


class MatchingEnterView(
    view_partials.RequiredMatchingPartial
):
    template_name = 'callisto_core/reporting/submission.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'
    admin_email_template_name = 'callisto_core/accounts/match_confirmation_callisto_team.html'


class MatchingWithdrawView(
    view_partials.MatchingWithdrawPartial,
):
    template_name = 'callisto_core/reporting/submission.html'
    access_template_name = 'callisto_core/delivery/form_redirect.html'
