from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site

from .forms import PageFormManager, PageForm
from .storage import SessionStorage
from .models import Page

# from django-formtools
# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE


class StepsHelper(object):
    done_name = 'done'

    def __init__(self, view):
        self.view = view

    @property
    def all(self):
        return self.view.form_manager.forms

    @property
    def step_count(self):
        return len(self.all)

    @property
    def current(self):
        return self._current_step or self.first

    @property
    def _current_step(self):
        return self.view.request.POST.get('wizard_current_step', None)

    @property
    def finished(self):
        return self.view.request.POST.get('wizard_goto_step', None) == 'Submit'

    @property
    def first(self):
        return 0

    @property
    def last(self):
        return self.all[-1].page_index

    @property
    def next(self):
        return self.step_key(1)

    @property
    def prev(self):
        return self.step_key(-1)

    @property
    def next_is_done(self):
        return self.next == self.done_name

    def step_key(self, adjustment):
        key = self.current + adjustment
        if self.step_count > key:
            return self.view.forms[key].page_index
        elif self.step_count == key:
            return self.done_name
        else:
            return None

    def url(self, step):
        kwargs = {'step': step}
        if self.object_to_edit:
            kwargs['edit_id'] = self.object_to_edit.id
        return reverse(self.url_name, kwargs=kwargs)


class RenderMixin(object):

    def render(self, **kwargs):
        if self.steps.finished:
            return self.render_done(**kwargs)
        else:
            return super().render(**kwargs)

    def render_next_step(self, **kwargs):
        self.storage.current_step = self.steps.next
        return redirect(self.steps.url(self.steps.next))

    def render_goto_step(self, goto_step, **kwargs):
        self.storage.current_step = goto_step
        return redirect(self.get_step_url(goto_step))

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
            return self.render_next_step(**kwargs)

    def form_invalid(self, form):
        return self.render(**kwargs)


class WizardView(RenderMixin, RoutingMixin, FormView):
    site_id = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object_to_edit = kwargs.get('object_to_edit')
        self.form_to_edit = self.get_form_to_edit(self.object_to_edit)

    @property
    def steps(self):
        return StepsHelper(self)

    @property
    def storage(self):
        return SessionStorage(self.request)

    @property
    def form_manager(self):
        return PageFormManager(get_current_site(self.request).id)

    @property
    def form(self):
        return self.get_form()

    @property
    def forms(self):
        return self.form_manager.forms

    def get_form(self):
        return self.forms[self.steps.current]

    @property
    def processed_answers(self):
        return [
            self.storage.get_step_data(form)
            for form in self.forms
        ]

    def get_form_to_edit(self, object_to_edit):
        return []

    def done(self, forms, **kwargs):
        if kwargs.get('step', None) != self.steps.done_name:
            return redirect(self.get_step_url(self.steps.done_name))
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
