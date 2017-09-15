'''

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/

views should define:
    - templates

'''
from . import view_partials
from .view_partials import WizardFormPartial  # NOQA, legacy support


class NewWizardView(
    view_partials.WizardRedirectPartial,
):
    step = 0


class WizardView(
    view_partials.WizardPartial,
):
    template_name = 'wizard_builder/wizard_form.html'
    done_template_name = 'wizard_builder/review.html'
