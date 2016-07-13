import json

from wizard_builder.views import ConfigurableFormWizard

# from .models import Report
from django.http import HttpResponse


class TestWizard(ConfigurableFormWizard):
    # def get_form_to_edit(self, object_to_edit):
    #     self.form_to_edit = object_to_edit.text

    def done(self, form_list, **kwargs):
        # report = Report()
        # if self.object_to_edit:
        #     report = self.object_to_edit
        # report.text = self.processed_answers
        # report.save()
        return HttpResponse(json.dumps(self.processed_answers))


def new_test_wizard_view(request, step=None):
    return TestWizard.wizard_factory().as_view(url_name="test_wizard", template_name='wizard_form.html')(request,
                                                                                                         step=step)


def edit_test_wizard_view(request, report_id, step=None):
    # report = Report.objects.get(id=report_id)
    report = None
    return TestWizard.wizard_factory(object_to_edit=report).as_view(url_name="test_wizard",
                                                                    template_name='wizard_form.html')(request,
                                                                                                      step=step)
