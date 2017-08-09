from collections import OrderedDict

from django.core.urlresolvers import reverse

from .forms import PageFormManager
from .models import Page
from .wizards import NamedUrlWizardView

# from django-formtools
# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE


class ConfigurableFormWizard(NamedUrlWizardView):

    def get_form_to_edit(self, object_to_edit):
        '''Takes the passed in object and returns a list of dicts representing the answered questions'''
        return []

    def __init__(self, *args, **kwargs):
        super(ConfigurableFormWizard, self).__init__(*args, **kwargs)
        # TODO: don't define self values before init???
        self.processed_answers = []
        self.form_to_edit = self.get_form_to_edit(self.object_to_edit)

    def post(self, *args, **kwargs):
        form_current_step = self.request.POST.get('current_step')
        if (
            form_current_step != self.steps.current and
            self.storage.current_step is not None
        ):
            # form refreshed, change current step
            self.storage.current_step = form_current_step

        # get the form for the current step
        form = self.get_form(data=self.request.POST, files=self.request.FILES)

        # and try to validate
        if form.is_valid():
            # if the form is valid, store the cleaned data and files.
            self.storage.set_step_data(
                self.steps.current,
                self.process_step(form),
            )
            self.storage.set_step_files(
                self.steps.current,
                self.process_step_files(form),
            )

            # this check was moved from beginning of the method (modification
            # from original)
            wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
            if wizard_goto_step and wizard_goto_step in self.get_form_list():
                return self.render_goto_step(wizard_goto_step)

            # check if the current step is the last step
            # render done if "skip to end" has been sent (modification from
            # original)
            if self.steps.current == self.steps.last or wizard_goto_step == "end":
                # no more steps, render done view
                return self.render_done(form, **kwargs)
            else:
                # proceed to the next step
                return self.render_next_step(form)
        return self.render(form)

    def process_answers(self, form_list):
        for form in form_list:
            self.processed_answers.append(form.processed)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        context.update({
            'page_count': self.page_count,
            'current_page': form.page_index,
            'editing': self.object_to_edit,
        })
        return context

    def _process_non_formset_answers_for_edit(self, json_questions):
        answers = {}
        for question in json_questions:
            answer = question.get('answer')
            question_id = question.get('id')
            if answer and question_id:
                # TODO: smell this string interpolation
                answers["question_%i" % question_id] = answer
                extra = question.get('extra')
                if extra:
                    extra_answer = extra.get('answer')
                    if extra_answer:
                        answers['question_%i_extra-%s' %
                                (question_id, answer)] = extra_answer
        return answers

    def _process_formset_answers_for_edit(self, json_questions, page_id):
        answers = []
        # TODO: smell this next
        formset = next(
            (i for i in json_questions if i.get('page_id') == page_id), None)
        if formset:
            for form in formset.get('answers'):
                answers.append(
                    self._process_non_formset_answers_for_edit(form))
        return answers

    def get_form_initial(self, step):
        if self.form_to_edit:
            return self._process_non_formset_answers_for_edit(
                self.form_to_edit,
            )
        else:
            return self.initial_dict.get(step, {})

    @classmethod
    def wizard_factory(cls, object_to_edit=None, site_id=None, **kwargs):
        pages = Page.objects.on_site(site_id).all()
        formsets = {}
        items = {}
        # TODO: make this for loop a manager method
        for idx, page in enumerate(pages):
            for question in page.questions:
                items[question.field_id] = question
        # TODO: smell this type
        return type(
            cls.__name__,
            (cls,),
            {
                "items": items,
                "form_list": PageFormManager.forms(pages),
                "object_to_edit": object_to_edit,
                "formsets": formsets,
                "page_count": len(pages),
            },
        )

    def get_prefix(self, request, *args, **kwargs):
        identifier = str(self.object_to_edit.id) if self.object_to_edit else ""
        return "form_wizard" + identifier

    def get_step_url(self, step):
        '''
            Passes record to edit along to the next step.
            Edit url must have a named 'edit_id' group
        '''
        kwargs = {'step': step}
        if self.object_to_edit:
            kwargs['edit_id'] = self.object_to_edit.id
        return reverse(self.url_name, kwargs=kwargs)

    def render_done(self, form, **kwargs):
        """
        This method gets called when all forms passed. The method should also
        re-validate all steps to prevent manipulation. If any form fails to
        validate, `render_revalidation_failure` should get called.
        If everything is fine call `done`.
        """
        final_forms = OrderedDict()
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key))
            # don't reject form if it's not bound (modification from original)
            if form_obj.is_bound and not form_obj.is_valid():
                return self.render_revalidation_failure(form_key,
                                                        form_obj,
                                                        **kwargs)
            final_forms[form_key] = form_obj

        # hook to allow processing of answers before done
        self.process_answers(final_forms.values())

        # render the done view and reset the wizard before returning the
        # response. This is needed to prevent from rendering done with the
        # same data twice.
        done_response = self.done(
            final_forms.values(),
            form_dict=final_forms,
            **kwargs)
        self.storage.reset()
        return done_response
