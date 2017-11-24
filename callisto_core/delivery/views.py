'''

Views specific to callisto-core, if you are implementing callisto-core
you SHOULD NOT be importing these views. Import from view_partials instead.
All of the classes in this file should represent one of more HTML view.

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/

views should define:
    - templates

'''
from django.contrib.auth import views as auth_views

from . import view_partials

################
# auth views   #
################


class LoginView(
    auth_views.LoginView,
):
    template_name = 'callisto_core/delivery/login.html'


################
# report views #
################


class ReportCreateView(
    view_partials.ReportCreatePartial,
):
    template_name = 'callisto_core/delivery/new_report.html'
    access_template_name = 'callisto_core/delivery/form.html'


class ReportDeleteView(
    view_partials.ReportDeletePartial,
):
    template_name = 'callisto_core/delivery/form.html'
    access_template_name = 'callisto_core/delivery/form.html'


################
# wizard views #
################


class EncryptedWizardView(
    view_partials.EncryptedWizardPartial,
):
    template_name = 'callisto_core/delivery/wizard_form.html'
    access_template_name = 'callisto_core/delivery/form.html'
    done_template_name = 'callisto_core/delivery/review.html'


#############
# dashboard #
#############


class DashboardView(
    view_partials.PassphraseClearingPartial,
):
    template_name = "callisto_core/delivery/dashboard/index.html"


class DashboardReportDeletedView(
    DashboardView,
):
    template_name = "callisto_core/delivery/dashboard/report_deleted.html"


class DashboardMatchingWithdrawnView(
    DashboardView,
):
    template_name = "callisto_core/delivery/dashboard/matching_withdrawn.html"


class DownloadPDFView(
    view_partials.DownloadPDFPartial,
):
    access_template_name = 'callisto_core/delivery/form.html'


class ViewPDFView(
    view_partials.ViewPDFPartial,
):
    access_template_name = 'callisto_core/delivery/form.html'
