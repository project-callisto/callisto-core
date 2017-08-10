from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .forms import PageFormManager
from .storage import SessionStorage

# from django-formtools
# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE


class StepsHelper(object):

    def __init__(self, wizard):
        self._wizard = wizard

    def __dir__(self):
        return self.all

    def __len__(self):
        return self.count

    @property
    def all(self):
        return self._wizard.form_list

    @property
    def count(self):
        return len(self.all)

    @property
    def current(self):
        return self._wizard.storage.current_step or self.first

    @property
    def first(self):
        "Returns the name of the first step."
        return self.all[0].page_index

    @property
    def last(self):
        "Returns the name of the last step."
        return self.all[-1].page_index

    def step_key(self, adjustment):
        keys = list(self._wizard.form_list.keys())
        key = self.step_key + adjustment
        if len(keys) > key:
            return keys[key]
        else:
            return None

    @property
    def next(self):
        return self.step_key(1)

    @property
    def prev(self):
        return self.step_key(-1)

    @property
    def step(self):
        return self._wizard.steps.current

    @property
    def index(self):
        return list(self._wizard.form_list.keys()).index(self.step)

    @property
    def step0(self):
        return int(self.index)

    @property
    def step1(self):
        return int(self.index) + 1


class RenderMixin(object):

    def render(self, form=None, **kwargs):
        form = form or self.form
        context = self.get_context_data(form=form, **kwargs)
        return self.render_to_response(context)

    def render_next_step(self, form, **kwargs):
        self.storage.current_step = self.steps.next
        return redirect(self.get_step_url(self.steps.next))

    def render_goto_step(self, goto_step, **kwargs):
        self.storage.current_step = goto_step
        return redirect(self.get_step_url(goto_step))

    def render_revalidation_failure(self, step, form, **kwargs):
        self.storage.current_step = step
        return redirect(self.get_step_url(step))

    def render_done(self, **kwargs):
        final_forms = [
            self.storage.get_step_data(form_key)
            for form_key in self.form_list
        ]
        self.process_answers(final_forms.values())
        return self.done(final_forms, **kwargs)


class RoutingMixin(object):

    def get(self, request, *args, **kwargs):
        step_url = kwargs.get('step', None)
        if step_url is None or 'reset' in self.request.GET:
            self.storage.init_data()
            return redirect(self.get_step_url(self.steps.current))
        elif step_url == self.done_step_name:
            return self.render_done(**kwargs)
        elif (
            step_url == self.steps.current or
            step_url in self.form_list
        ):
            return self.render(self.form, **kwargs)
        else:
            self.storage.current_step = self.steps.first
            return redirect(self.get_step_url(self.steps.first))

    def post(self, *args, **kwargs):
        step = self.request.POST.get('current_step')
        if (
            step != self.steps.current and
            self.storage.current_step is not None
        ):
            self.storage.current_step = step

    def form_valid(self, form, **kwargs):
        step = self.request.POST.get('wizard_goto_step', None)
        self.storage.set_step_data(
            self.steps.current,
            form.data,
        )
        if step in self.form_list:
            return self.render_goto_step(step)
        if self.steps.current == self.steps.last or step == "end":
            return self.render_done(**kwargs)
        else:
            return self.render_next_step(form)

    def form_invalid(self, form):
        return self.render(form)


class WizardView(RenderMixin, RoutingMixin, TemplateView):
    form_list = None
    initial_dict = None
    instance_dict = None
    condition_dict = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'
    done_step_name = 'done'
    site_id = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_answers = []
        self.object_to_edit = kwargs.get('object_to_edit')
        self.form_to_edit = self.get_form_to_edit(self.object_to_edit)
        self.form_list, self.items = PageFormManager.setup(kwargs['site_id'])

    @property
    def steps(self):
        return StepsHelper(self)

    @property
    def storage(self):
        return SessionStorage(self.request)

    @property
    def form(self):
        return self.form_list[self.steps.current]

    def get_form_instance(self, step):
        return self.instance_dict.get(step, None)

    def get_form_to_edit(self, object_to_edit):
        return []

    def process_answers(self, form_list):
        for form in form_list:
            self.processed_answers.append(form.processed)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        context.update(self.storage.extra_data)
        context.update({
            'page_count': self.page_count,
            'current_page': form.page_index,
            'editing': self.object_to_edit,
            'wizard': {
                'form': form,
                'steps': self.steps,
                'current_step': self.steps.current,
                'url_name': self.url_name,
            }
        })
        return context

    def get_form_initial(self, step):
        if self.form_to_edit:
            return self._process_non_formset_answers_for_edit(
                self.form_to_edit,
            )
        else:
            return self.initial_dict.get(step, {})

    def get_step_url(self, step):
        kwargs = {'step': step}
        if self.object_to_edit:
            kwargs['edit_id'] = self.object_to_edit.id
        return reverse(self.url_name, kwargs=kwargs)

    def done(self, form_list, **kwargs):
        if kwargs.get('step', None) != self.done_step_name:
            return redirect(self.get_step_url(self.done_step_name))
        else:
            return self.render_done(**kwargs)

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
