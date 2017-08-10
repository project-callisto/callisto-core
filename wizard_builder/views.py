from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.http import JsonResponse

from .forms import PageFormManager
from .storage import SessionStorage

# from django-formtools
# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE


class StepsHelper(object):
    current_step = None

    def __init__(self, wizard):
        self._wizard = wizard

    @property
    def all(self):
        return self._wizard.forms

    @property
    def current(self):
        return self.current_step or self.first

    @property
    def first(self):
        return self.all[0].page_index

    @property
    def last(self):
        return self.all[-1].page_index

    def step_key(self, adjustment):
        key = self.current + adjustment
        if len(self._wizard.forms) > key:
            return self._wizard.forms[key]
        else:
            return None

    @property
    def next(self):
        return self.step_key(1)

    @property
    def prev(self):
        return self.step_key(-1)

    @property
    def index(self):
        return list(self._wizard.forms.keys()).index(self.current)

    @property
    def step0(self):
        return int(self.index)

    @property
    def step1(self):
        return int(self.index) + 1


class RenderMixin(object):

    def render(self, **kwargs):
        if kwargs.get('step', None) == self.done_step_name:
            return self.render_done(**kwargs)
        else:
            return super().render(**kwargs)

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
        return JsonResponse(self.processed_answers)


class RoutingMixin(object):

    def get(self, request, *args, **kwargs):
        if kwargs.get('step', None) or 'reset' in self.request.GET:
            self.storage.init_data()
        return super().get(request, *args, **kwargs)

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
        if step in self.forms:
            return self.render_goto_step(step)
        if self.steps.current == self.steps.last or step == "end":
            return self.render_done(**kwargs)
        else:
            return self.render_next_step(form)

    def form_invalid(self, form):
        return self.render(form)


class WizardView(RenderMixin, RoutingMixin, TemplateView):
    forms = None
    initial_dict = None
    instance_dict = None
    condition_dict = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'
    done_step_name = 'done'
    site_id = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object_to_edit = kwargs.get('object_to_edit')
        self.form_to_edit = self.get_form_to_edit(self.object_to_edit)
        self.forms, self.items = PageFormManager.setup(kwargs['site_id'])

    @property
    def steps(self):
        return StepsHelper(self)

    @property
    def storage(self):
        return SessionStorage(self.request)

    @property
    def form(self):
        return self.forms[self.steps.current]

    def get_form_instance(self, step):
        return self.instance_dict.get(step, None)

    def get_form_to_edit(self, object_to_edit):
        return []

    @property
    def processed_answers(self):
        return [
            self.storage.get_step_data(form)
            for form in self.forms
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.storage.extra_data)
        context.update({
            'form': self.form,
            'page_count': len(self.forms),
            'current_page': self.form.page_index,
            'editing': self.object_to_edit,
            'wizard': {
                'form': self.form,
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

    def done(self, forms, **kwargs):
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
