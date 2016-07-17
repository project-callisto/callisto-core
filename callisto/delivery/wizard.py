import json
import logging

from wizard_builder.forms import get_form_pages
from wizard_builder.views import ConfigurableFormWizard

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseServerError

from callisto.evaluation.models import EvalRow

from .forms import NewSecretKeyForm, SecretKeyForm
from .models import Report

logger = logging.getLogger(__name__)


class EncryptedFormBaseWizard(ConfigurableFormWizard):

    def get_form_initial(self, step):
        # TODO: store decrypted record with other intermediate form data
        # https://github.com/SexualHealthInnovations/callisto-core/issues/33
        if self.object_to_edit and step and step != '0' and not self.form_to_edit:
            # decrypt record and store in memory
            cleaned_data = self.get_cleaned_data_for_step('0')
            if cleaned_data:
                key = cleaned_data.get('key')
                self.form_to_edit = json.loads(self.object_to_edit.decrypted_report(key))
        return super(EncryptedFormBaseWizard, self).get_form_initial(step)

    @classmethod
    def get_key_form(cls, record_to_edit):
        if record_to_edit:
            return type('EditSecretKeyForm', (SecretKeyForm,), {'report': record_to_edit})
        else:
            return NewSecretKeyForm

    @classmethod
    def generate_form_list(cls, page_map, pages, record_to_edit, **kwargs):
        form_list = get_form_pages(page_map)
        form_list.insert(0, cls.get_key_form(record_to_edit))
        return form_list

    @classmethod
    def calculate_real_page_index(cls, raw_idx, pages, record_to_edit, **kwargs):
        # add one for key creation/entry page
        return raw_idx + 1

    def wizard_complete(self, report, **kwargs):
        """
        This method must be overridden by a subclass to redirect wizard after the report has been processed.
        """
        raise NotImplementedError("Your %s class has not defined a wizard_complete() "
                                  "method, which is required." % self.__class__.__name__)

    def _unauthorized_access(self, req, report):
        logger.error("user {} and report {} don't match in wizard.done".format(req.user, report.id))
        return HttpResponseForbidden() if settings.DEBUG else HttpResponseServerError()

    def done(self, form_list, **kwargs):
        req = kwargs.get('request') or self.request

        if self.object_to_edit:
            report = self.object_to_edit
        elif self.storage.extra_data.get('report_id'):
            report = Report.objects.get(id=self.storage.extra_data.get('report_id'))
        else:
            report = Report(owner=req.user)

        if not report.owner == req.user:
            self._unauthorized_access(req, report)

        key = list(form_list)[0].cleaned_data['key']

        report_text = json.dumps(self.processed_answers, sort_keys=True)
        report.encrypt_report(report_text, key, self.object_to_edit)
        report.save()

        # save anonymised answers
        if self.object_to_edit:
            EvalRow.store_eval_row(action=EvalRow.EDIT, report=report, decrypted_text=report_text)
        else:
            EvalRow.store_eval_row(action=EvalRow.CREATE, report=report, decrypted_text=report_text)

        return self.wizard_complete(report, **kwargs)

    def get_template_names(self):
        # render key page with separate template
        if self.steps.current == self.steps.first:
            if self.object_to_edit:
                return ['decrypt_record_for_edit.html']
            else:
                return ['create_key.html']
        else:
            return ['record_form.html']

    def auto_save(self, **kwargs):
        '''Automatically save what's been entered so far before rendering the next step'''
        if not self.object_to_edit and int(self.steps.current) > 0:
            form_list = self.get_form_list()
            forms_so_far = {}
            for form_key in form_list:
                form_obj = self.get_form(
                    step=form_key,
                    data=self.storage.get_step_data(form_key),
                    files=self.storage.get_step_files(form_key)
                )
                form_obj.is_valid()
                forms_so_far[form_key] = form_obj
            if self.storage.extra_data.get('report_id'):
                report = Report.objects.get(id=self.storage.extra_data.get('report_id'))
            else:
                req = kwargs.get('request') or self.request
                report = Report(owner=req.user)
            report_text = json.dumps(self.process_answers(forms_so_far.values(), form_dict=forms_so_far),
                                     sort_keys=True)
            key = forms_so_far['0'].cleaned_data['key']
            report.encrypt_report(report_text, key, edit=self.object_to_edit, autosave=True)
            report.save()
            self.storage.extra_data['report_id'] = report.id

    def render(self, form=None, **kwargs):
        self.auto_save()
        return super(EncryptedFormBaseWizard, self).render(form, **kwargs)

    def get(self, *args, **kwargs):
        """
        Restart the wizard (including associated autosaved record) when the first page is requested
        """
        step_url = kwargs.get('step', None)
        if step_url is None or step_url == '0':
            self.storage.reset()
            self.storage.current_step = self.steps.first
        return super(EncryptedFormBaseWizard, self).get(*args, **kwargs)
