from formtools.wizard.views import NamedUrlSessionWizardView
from formtools.wizard.forms import ManagementForm
from collections import OrderedDict
from django.core.exceptions import ValidationError
from django.forms.formsets import BaseFormSet
from functools import partial
from django.utils.html import conditional_escape, mark_safe

from .forms import get_form_pages, QuestionPageForm
from .models import QuestionPage, TextPage, Conditional, PageBase


# rearranged from django-formtools to allow binding forms before skipping steps & submission
# adds hook before done is called to process answers

# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE
class ModifiedSessionWizardView(NamedUrlSessionWizardView):
    def __init__(self, **kwargs):
        super(ModifiedSessionWizardView, self).__init__(**kwargs)
        self.processed_answers = []

    def post(self, *args, **kwargs):
        # Check if form was refreshed
        management_form = ManagementForm(self.request.POST, prefix=self.prefix)
        if not management_form.is_valid():
            raise ValidationError(
                'ManagementForm data is missing or has been tampered.',
                code='missing_management_form',
            )

        form_current_step = management_form.cleaned_data['current_step']
        if (form_current_step != self.steps.current and
                self.storage.current_step is not None):
            # form refreshed, change current step
            self.storage.current_step = form_current_step

        # get the form for the current step
        form = self.get_form(data=self.request.POST, files=self.request.FILES)

        # and try to validate
        if form.is_valid():
            # if the form is valid, store the cleaned data and files.
            self.storage.set_step_data(self.steps.current,
                                       self.process_step(form))
            self.storage.set_step_files(self.steps.current,
                                        self.process_step_files(form))

            # this check was moved from beginning of the method (modification from original)
            wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
            if wizard_goto_step and wizard_goto_step in self.get_form_list():
                return self.render_goto_step(wizard_goto_step)

            # check if the current step is the last step
            if self.steps.current == self.steps.last:
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
            form_obj = self.get_form(step=form_key,
                                     data=self.storage.get_step_data(form_key),
                                     files=self.storage.get_step_files(form_key))
            # don't reject form if it's not bound (modification from original)
            if form_obj.is_bound and not form_obj.is_valid():
                return self.render_revalidation_failure(form_key,
                                                        form_obj,
                                                        **kwargs)
            final_forms[form_key] = form_obj

        # hook to allow processing of answers before done
        self.processed_answers = self.process_answers(final_forms.values(),
                                                      form_dict=final_forms)

        # render the done view and reset the wizard before returning the
        # response. This is needed to prevent from rendering done with the
        # same data twice.
        done_response = self.done(final_forms.values(),
                                  form_dict=final_forms,
                                  **kwargs)
        self.storage.reset()
        return done_response


class ConfigurableFormWizard(ModifiedSessionWizardView):
    def get_form_to_edit(self, object_to_edit):
        return []

    def __init__(self, *args, **kwargs):
        super(ConfigurableFormWizard, self).__init__(*args, **kwargs)
        self.form_to_edit = self.get_form_to_edit(self.object_to_edit)

    def process_answers(self, form_list, form_dict):
        def process_form(cleaned_data, output_location):
            # order by position on page (python & json lists both preserve order)
            questions = [(field_name, answer, self.items[field_name]) for field_name, answer in cleaned_data.items()
                         if "extra" not in field_name]
            questions.sort(key=lambda x: x[2].position)
            for field_name, answer, question in questions:
                extra_key = "%s_extra-%s" % (field_name, answer)
                extra_prompt = self.items.get(extra_key)
                extra_context = None
                if extra_prompt:
                    extra_context = {'answer': conditional_escape(cleaned_data.get(extra_key, '')),
                                     'extra_text': extra_prompt}

                output_location.append(question.serialize_for_report(answer, extra_context))

        answered_questions = []
        for idx, form in form_dict.items():
            if isinstance(form, QuestionPageForm):
                try:
                    clean_data = form.cleaned_data
                except:
                    # process unbound form with initial data
                    initial_data = self.get_form_initial(str(idx))
                    clean_data = dict([(field, initial_data.get(field, '')) for field in form.fields.keys()])
                process_form(clean_data, answered_questions)
            elif isinstance(form, BaseFormSet):
                try:
                    clean_data = form.cleaned_data
                except:
                    # process unbound formset with initial data
                    clean_data = self.get_form_initial(str(idx))
                formset_answers = []
                for entry in clean_data:
                    entry_answers = []
                    process_form(entry, entry_answers)
                    formset_answers.append(entry_answers)
                answered_questions.append({'type': 'FormSet',
                                           'page_id': form.page_id,
                                           'prompt': form.name_for_multiple,
                                           'section': form.page_section,
                                           'answers': formset_answers})
        return answered_questions

    def get_context_data(self, form, **kwargs):
        context = super(ConfigurableFormWizard, self).get_context_data(form=form, **kwargs)
        if isinstance(form, QuestionPageForm) or isinstance(form, BaseFormSet):
            context.update({'page_count': self.page_count,
                            'current_page': self.page_count_map.get(form.page_index),
                            'editing': self.object_to_edit})
        return context

    def _process_non_formset_answers_for_edit(self, json_questions):
        answers = {}
        for question in json_questions:
            answer = question.get('answer')
            question_id = question.get('id')
            if answer and question_id:
                answers["question_%i" % question_id] = mark_safe(answer)  # answers are escaped before saving
                extra = question.get('extra')
                if extra:
                    extra_answer = extra.get('answer')
                    if extra_answer:
                        answers['question_%i_extra-%s' % (question_id, answer)] = mark_safe(extra_answer)
        return answers

    def _process_formset_answers_for_edit(self, json_questions, page_id):
        answers = []
        formset = next((i for i in json_questions if i.get('page_id') == page_id), None)
        if formset:
            for form in formset.get('answers'):
                answers.append(self._process_non_formset_answers_for_edit(form))
        return answers

    def get_form_initial(self, step):
        if self.form_to_edit:
            form = self.form_list[step]
            # process formset answers
            if issubclass(form, QuestionPageForm):
                return self._process_non_formset_answers_for_edit(self.form_to_edit)
            elif issubclass(self.form_list[step], BaseFormSet):
                page_id = self.formsets.get(step)
                return self._process_formset_answers_for_edit(self.form_to_edit, page_id)
        else:
            return self.initial_dict.get(step, {})

    @classmethod
    def generate_form_list(cls, page_map, pages, object_to_edit, **kwargs):
        return get_form_pages(page_map)

    # allows you to append pages to the form like a password field
    @classmethod
    def calculate_real_page_index(cls, raw_idx, pages, object_to_edit, **kwargs):
        return raw_idx

    @classmethod
    def wizard_factory(cls, object_to_edit=None, **kwargs):
        pages = PageBase.objects.all()
        form_items_at_initialization = {}
        page_map = []
        formsets = {}
        page_index = dict([(page.pk, cls.calculate_real_page_index(idx, pages, object_to_edit, **kwargs))
                           for idx, page in enumerate(pages)])
        condition_dict = {}
        page_count = 0
        for idx, page in enumerate(pages):
            real_page_idx = cls.calculate_real_page_index(idx, pages, object_to_edit, **kwargs)
            if isinstance(page, QuestionPage):
                # increment page count
                page_count += 1
                # store question copies
                questions = page.formquestion_set.order_by('position')
                if len(questions) > 0:
                    question_copies = [question.clone() for question in questions]
                    page_map.append((page, question_copies))
                    for question_copy in question_copies:
                        form_items_at_initialization["question_%s" % question_copy.pk] = question_copy
                        extras = question_copy.get_extras()
                        if extras:
                            for (extra_id, prompt) in extras:
                                form_items_at_initialization[extra_id] = prompt
                # store page_id if is formset
                if page.multiple:
                    formsets[str(real_page_idx)] = page.pk
            elif isinstance(page, TextPage):
                page_map.append((page, []))
            # populate condition dict
            try:
                condition = page.conditional
                depends_on_question = condition.question
                depends_on_page = depends_on_question.page
                depends_on_page_idx = page_index[depends_on_page.pk]
                depends_on_question_field = "question_%s" % depends_on_question.pk
                condition_dict[str(real_page_idx)] = partial(predicate, condition, depends_on_page_idx,
                                                             depends_on_question_field)
            except Conditional.DoesNotExist:
                pass

        form_list = cls.generate_form_list(page_map, pages, object_to_edit, **kwargs)
        page_count_map = calculate_page_count_map(pages)

        # storage is generated by class name, so want unique class names per object edited for edit forms
        return type('FormWizard' + (str(object_to_edit.id) if object_to_edit else ""), (cls,),
                    {"items": form_items_at_initialization,
                     "form_list": form_list,
                     "object_to_edit": object_to_edit,
                     "formsets": formsets,
                     "condition_dict": condition_dict,
                     "page_count": page_count_map['page_count'],
                     "page_count_map": page_count_map})


def predicate(passed_condition, depends_on_page_idx, depends_on_question_field, wizard):
    cleaned_data = wizard.get_cleaned_data_for_step(str(depends_on_page_idx)) \
                   or {depends_on_question_field: 'none'}
    condition_type = passed_condition.condition_type

    form_answer = cleaned_data.get(depends_on_question_field)
    if (len(form_answer)) < 1:
        form_answer = "none"

    if condition_type == Conditional.EXACTLY:
        if not isinstance(form_answer, str):
            form_answer = ','.join(form_answer)

        condition_answer = passed_condition.answer
        if not isinstance(condition_answer, str):
            condition_answer = ','.join(condition_answer)

        return form_answer == condition_answer
    else:
        if isinstance(form_answer, str):
            form_answer = [form_answer]
        possibles = passed_condition.answer.split(',')
        # return true if intersection of answers & possibles is non-empty
        return len(list(set(form_answer) & set(possibles))) > 0


def calculate_page_count_map(pages):
    page_count = 0
    depends_on_seen = []
    page_count_map = {}
    for idx, page in enumerate(pages):
        if isinstance(page, QuestionPage):
            try:
                condition = page.conditional
                depends_on_question = condition.question
                if depends_on_question not in depends_on_seen:
                    page_count += 1
                    depends_on_seen.append(depends_on_question)
            except Conditional.DoesNotExist:
                page_count += 1
            page_count_map[idx] = page_count
    page_count_map['page_count'] = page_count
    return page_count_map
