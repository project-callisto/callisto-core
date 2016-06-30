import json
import logging

from wizard_builder.forms import get_form_pages
from wizard_builder.views import ConfigurableFormWizard

from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden

from callisto.evaluation.models import EvalRow

from .forms import NewSecretKeyForm, SecretKeyForm
from .models import Report

logger = logging.getLogger(__name__)

class EncryptedFormBaseWizard(ConfigurableFormWizard):

    def get_form_initial(self, step):
        # TODO: store decrypted record with other intermediate form data
        # https://github.com/SexualHealthInnovations/callisto-core/issues/33
        if self.object_to_edit and step and step !='0' and not self.form_to_edit:
            #decrypt record and store in memory
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
        if record_to_edit:
            form_list.insert(0, cls.get_key_form(record_to_edit))
        form_list.append(cls.get_key_form(record_to_edit))
        return form_list

    @classmethod
    def calculate_real_page_index(cls, raw_idx, pages, record_to_edit, **kwargs):
        #add one for decryption page if editing
        return raw_idx + 1 if record_to_edit else raw_idx

    def wizard_complete(self, report, **kwargs):
        """
        This method must be overridden by a subclass to redirect wizard after the report has been processed.
        """
        raise NotImplementedError("Your %s class has not defined a wizard_complete() "
            "method, which is required." % self.__class__.__name__)

    def done(self, form_list, **kwargs):
        req = kwargs.get('request') or self.request
        report = Report(owner=req.user)
        if self.object_to_edit:
            if self.object_to_edit.owner == req.user:
                report = self.object_to_edit
            else:
                return HttpResponseForbidden()

        key = list(form_list)[-1].cleaned_data['key']

        report_text = json.dumps(self.processed_answers, sort_keys=True)
        report.encrypt_report(report_text, key)
        report.save()

        #save anonymised answers
        try:
            if self.object_to_edit:
                action = EvalRow.EDIT
            else:
                action = EvalRow.CREATE
            row = EvalRow()
            row.anonymise_record(action=action, report=report, decrypted_text=report_text)
            row.save()
        except Exception as e:
            logger.error(e)
            pass

        return self.wizard_complete(report, **kwargs)

    def get_template_names(self):
         # render key page with separate template
         if self.object_to_edit and self.steps.current == self.steps.first:
            return ['decrypt_record_for_edit.html']
         elif self.object_to_edit and self.steps.current == self.steps.last:
            return ['encrypt_record_for_edit.html']
         elif self.steps.current == self.steps.last:
            return ['create_key.html']
         else:
            return ['record_form.html']

    def get_step_url(self, step):
        kwargs={'step': step,}
        if self.object_to_edit:
            kwargs['report_id'] = self.object_to_edit.id
        return reverse(self.url_name, kwargs=kwargs)
