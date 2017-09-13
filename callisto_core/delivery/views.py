'''

Views specific to callisto-core, if you are implementing callisto-core
you SHOULD NOT be importing these views. Import from view_partials instead.
All of the classes in this file should represent one of more HTML view.

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/

views should define:
    - templates
    - "advanced" redirect urls

and should not define:
    - "basic" redirect urls, which should be in urls.py

'''
from django.core.urlresolvers import reverse

from . import view_partials

################
# report views #
################


class ReportCreateView(
    view_partials.ReportCreatePartial,
):
    template_name = 'callisto_core/delivery/form.html'
    access_template_name = 'callisto_core/delivery/form.html'

    def get_success_url(self):
        return reverse(
            'report_update',
            kwargs={'step': 0, 'uuid': self.object.uuid},
        )


class ReportDeleteView(
    view_partials.ReportDeletePartial,
):
    template_name = 'callisto_core/delivery/form.html'
    access_template_name = 'callisto_core/delivery/form.html'

    def view_action(self):
        self.report.delete()


################
# wizard views #
################


class EncryptedWizardView(
    view_partials.ReportUpdatePartial,
):
    template_name = 'callisto_core/delivery/wizard_form.html'
    done_template_name = 'callisto_core/delivery/review.html'


class WizardPDFView(
    view_partials.WizardPDFPartial,
):

    def get(self, *args, **kwargs):
        return self.report_pdf_response()
