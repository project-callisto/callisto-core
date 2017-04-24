import json

from wizard_builder.views import ConfigurableFormWizard

from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site

from .models import Report


class TestWizard(ConfigurableFormWizard):

    def get_form_to_edit(self, object_to_edit):
        if object_to_edit:
            return json.loads(object_to_edit.text)
        else:
            return super(TestWizard, self).get_form_to_edit(object_to_edit)

    def done(self, form_list, **kwargs):
        report = Report()
        if self.object_to_edit:
            report = self.object_to_edit
        report.text = self.processed_answers
        report.save()
        return HttpResponse(json.dumps(self.processed_answers))


def new_test_wizard_view(request, step=None):
    site = get_current_site(request)
    return TestWizard.wizard_factory(
        site_id=site.id,
    ).as_view(
        url_name="test_wizard",
        template_name='wizard_form.html',
    )(
        request,
        step=step,
    )


def edit_test_wizard_view(request, edit_id, step=None):
    report = Report.objects.get(id=edit_id)
    site = get_current_site(request)
    return TestWizard.wizard_factory(
        site_id=site.id,
        object_to_edit=report,
    ).as_view(
        url_name="test_edit_wizard",
        template_name='wizard_form.html',
    )(
        request,
        step=step,
    )
