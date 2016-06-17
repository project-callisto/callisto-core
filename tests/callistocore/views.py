from callisto.delivery.models import Report

from .forms import EncryptedFormWizard


def new_test_report_view(request, step=None):
    return EncryptedFormWizard.wizard_factory().as_view(url_name="test_new_report")(request, step=step)


def edit_test_report_view(request, report_id, step=None):
    report = Report.objects.get(id=report_id)
    return EncryptedFormWizard.wizard_factory(object_to_edit=report).as_view(url_name="test_edit_report")(request,
                                                                                                          step=step)
