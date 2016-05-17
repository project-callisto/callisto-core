import json
import bugsnag
from django.shortcuts import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.conf import settings

from .models import Report
from .forms import NewSecretKeyForm, SecretKeyForm

from evaluation.models import EvalRow
from reports.views import ConfigurableFormWizard
from reports.forms import get_record_form_pages


class EncryptedBaseWizard(ConfigurableFormWizard):

    def get_form_initial(self, step):
        #TODO: store with other intermediate form data
        if self.object_to_edit and step and step !='0' and not self.form_to_edit:
            #decrypt record and store in memory
            cleaned_data = self.get_cleaned_data_for_step('0')
            if cleaned_data:
                key = cleaned_data.get('key')
                self.form_to_edit = json.loads(self.object_to_edit.decrypted_report(key))
        return super().get_form_initial(step)

    @classmethod
    def get_key_form(cls, record_to_edit):
        if record_to_edit:
            return type('EditSecretKeyForm', (SecretKeyForm,), {'report': record_to_edit})
        else:
            return NewSecretKeyForm

    @classmethod
    def generate_form_list(cls, page_map, pages, record_to_edit, **kwargs):
        form_list = get_record_form_pages(page_map)
        if record_to_edit:
            form_list.insert(0, cls.get_key_form(record_to_edit))
        form_list.append(cls.get_key_form(record_to_edit))
        return form_list

    @classmethod
    def calculate_real_page_index(cls, raw_idx, pages, record_to_edit, **kwargs):
        #add one for decryption page if editing
        return raw_idx + 1 if record_to_edit else raw_idx

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
            #TODO: real logging
            bugsnag.notify(e)
            pass

        #TODO: check if valid?
        return HttpResponseRedirect(reverse('dashboard'))

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

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context.update({'school_name': settings.SCHOOL_SHORTNAME,
                        'full_school_name': settings.SCHOOL_LONGNAME,
                        'show_encouragement': settings.SHOW_ENCOURAGEMENT})
        return context

    def get_step_url(self, step):
        kwargs={'step': step,}
        if self.object_to_edit:
            kwargs['report_id'] = self.object_to_edit.id
        return reverse(self.url_name, kwargs=kwargs)