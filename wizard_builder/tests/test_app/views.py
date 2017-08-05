import json

from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse

from ...views import ConfigurableFormWizard
from .models import Report


class WizardTestApp(ConfigurableFormWizard):

    def get_form_to_edit(self, object_to_edit):
        if object_to_edit:
            return json.loads(object_to_edit.text)
        else:
            return super(WizardTestApp, self).get_form_to_edit(object_to_edit)

    def done(self, form_list, **kwargs):
        report = Report()
        if self.object_to_edit:
            report = self.object_to_edit
        report.text = self.processed_answers
        report.save()
        return HttpResponse(json.dumps(self.processed_answers))


def new_test_wizard_view(request, step=None):
    site = get_current_site(request)
    return WizardTestApp.wizard_factory(
        site_id=site.id,
    ).as_view(
        url_name=request.resolver_match.url_name,
    )(
        request,
        step=step,
    )


def edit_test_wizard_view(request, edit_id, step=None):
    report = Report.objects.get(id=edit_id)
    site = get_current_site(request)
    return WizardTestApp.wizard_factory(
        site_id=site.id,
        object_to_edit=report,
    ).as_view(
        url_name=request.resolver_match.url_name,
    )(
        request,
        step=step,
    )
