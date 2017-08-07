from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.forms.formsets import BaseFormSet

from .forms import PageForm, get_form_pages
from .models import Page
from .wizards import NamedUrlWizardView

# from django-formtools
# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE


class ModifiedSessionWizardView(NamedUrlWizardView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.processed_answers = []

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

    def process_answers(self, form_list, form_dict):
        return []

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
        self.processed_answers = self.process_answers(
            final_forms.values(),
            form_dict=final_forms,
        )

        # render the done view and reset the wizard before returning the
        # response. This is needed to prevent from rendering done with the
        # same data twice.
        done_response = self.done(
            final_forms.values(),
            form_dict=final_forms,
            **kwargs)
        self.storage.reset()
        return done_response


class ConfigurableFormWizard(ModifiedSessionWizardView):

    def get_form_to_edit(self, object_to_edit):
        '''Takes the passed in object and returns a list of dicts representing the answered questions'''
        return []

    def __init__(self, *args, **kwargs):
        super(ConfigurableFormWizard, self).__init__(*args, **kwargs)
        self.form_to_edit = self.get_form_to_edit(self.object_to_edit)

    def process_answers(self, form_list, form_dict):
        # TODO: smell this function
        def process_form(cleaned_data, output_location):
            # order by position on page (python & json lists both preserve
            # order)
            questions = []
            for field_name, answer in cleaned_data.items():
                if "extra" not in field_name:
                    questions.append(
                        (field_name, answer, self.items[field_name]))
            questions.sort(key=lambda x: x[2].position)
            for field_name, answer, question in questions:
                extra_key = "%s_extra-%s" % (field_name, answer)
                extra_prompt = self.items.get(extra_key)
                extra_context = None
                if extra_prompt:
                    extra_context = {
                        'answer': cleaned_data.get(extra_key, ''),
                        'extra_text': extra_prompt,
                    }

                output_location.append(
                    question.serialize_for_report(
                        answer, extra_context))

        answered_questions = []
        for idx, form in form_dict.items():
            if isinstance(form, PageForm):
                try:
                    clean_data = form.cleaned_data
                # process unbound form with initial data
                except BaseException:
                    initial_data = self.get_form_initial(str(idx))
                    clean_data = dict([(field, initial_data.get(field, ''))
                                       for field in form.fields.keys()])
                process_form(clean_data, answered_questions)
            elif isinstance(form, BaseFormSet):
                try:
                    clean_data = form.cleaned_data
                # process unbound formset with initial data
                except BaseException:
                    clean_data = self.get_form_initial(str(idx))
                formset_answers = []
                for entry in clean_data:
                    entry_answers = []
                    process_form(entry, entry_answers)
                    formset_answers.append(entry_answers)
                answered_questions.append({
                    'type': 'FormSet',
                    'page_id': form.page_id,
                    'prompt': form.name_for_multiple,
                    'section': form.page_section,
                    'answers': formset_answers,
                })
        return answered_questions

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        # TODO: smell these isinstance calls
        if isinstance(form, PageForm) or isinstance(form, BaseFormSet):
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
            form = self.form_list[step]
            # process formset answers
            # TODO: smell this issubclass
            if issubclass(form, PageForm):
                return self._process_non_formset_answers_for_edit(
                    self.form_to_edit)
            elif issubclass(self.form_list[step], BaseFormSet):
                page_id = self.formsets.get(step)
                return self._process_formset_answers_for_edit(
                    self.form_to_edit, page_id)
        else:
            return self.initial_dict.get(step, {})

    @classmethod
    def generate_form_list(cls, pages, object_to_edit, **kwargs):
        return get_form_pages(pages)

    @classmethod
    def wizard_factory(cls, object_to_edit=None, site_id=None, **kwargs):
        pages = Page.objects.on_site(site_id).all()
        form_list = cls.generate_form_list(pages, object_to_edit, **kwargs)
        formsets = {}
        items = {}
        # TODO: smell the positioning of this for loop
        for idx, page in enumerate(pages):
            for question in page.questions:
                items[question.field_id] = question
                extras = question.get_extras()
                if extras:
                    for (extra_id, prompt) in extras:
                        items[extra_id] = prompt
            if page.multiple:
                formsets[str(idx)] = page.pk
        # TODO: smell this type
        return type(
            cls.__name__,
            (cls,),
            {
                "items": items,
                "form_list": form_list,
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
