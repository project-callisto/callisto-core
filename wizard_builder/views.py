import logging
import traceback

from django.core.urlresolvers import reverse, reverse_lazy
from django.http.response import HttpResponseRedirect, JsonResponse
from django.views import generic as views

from .managers import FormManager

logger = logging.getLogger(__name__)


class NewWizardView(views.base.RedirectView):
    url = reverse_lazy(
        'wizard_update',
        kwargs={'step': 0},
    )


class StepsHelper(object):
    done_name = 'done'
    review_name = 'Review'
    next_name = 'Next'
    back_name = 'Back'

    def __init__(self, view):
        self.view = view

    @property
    def all(self):
        return self.view.manager.forms

    @property
    def step_count(self):
        return len(self.all)

    @property
    def current(self):
        _step = self._current or self.first
        if _step == self.done_name:
            return _step
        elif _step <= self.last:
            return _step
        else:
            return self.last

    @property
    def _current(self):
        _step = self.view.request.session.get('current_step', self.first)
        if _step == self.done_name:
            return _step
        else:
            return int(_step)

    @property
    def _goto_step_back(self):
        return self._goto_step(self.back_name)

    @property
    def _goto_step_next(self):
        return self._goto_step(self.next_name)

    @property
    def _goto_step_review(self):
        return self._goto_step(self.review_name)

    @property
    def first(self):
        return 0

    @property
    def last(self):
        return self.all[-1].manager_index

    @property
    def next(self):
        return self.adjust_step(1)

    @property
    def prev(self):
        return self.adjust_step(0)

    @property
    def next_is_done(self):
        return self.next == self.done_name

    @property
    def current_is_done(self):
        return self.current == self.done_name

    @property
    def current_url(self):
        return self.url(self.current)

    @property
    def last_url(self):
        return self.url(self.last)

    @property
    def done_url(self):
        return self.url(self.done_name)

    def _goto_step(self, step_type):
        post = self.view.request.POST
        return post.get('wizard_goto_step', None) == step_type

    def url(self, step):
        return reverse(
            self.view.request.resolver_match.view_name,
            kwargs={'step': step},
        )

    def overflowed(self, step):
        return int(step) > int(self.last)

    def finished(self, step):
        return self._goto_step_review or step == self.done_name

    def set_from_get(self, step_url_param):
        step = step_url_param or self.current
        self.view.request.session['current_step'] = step

    def set_from_post(self):
        step = self.view.request.POST.get('wizard_current_step', self.current)
        if self._goto_step_back:
            step = self.adjust_step(-1)
        if self._goto_step_next:
            step = self.adjust_step(1)
        self.view.request.session['current_step'] = step

    def adjust_step(self, adjustment):
        # TODO: tests as spec
        key = self.current + adjustment
        if key < self.first:
            return None
        if key == self.first:
            return self.first
        elif self.step_count > key:
            return self.view.manager.forms[key].manager_index
        elif self.step_count == key:
            return self.done_name
        else:
            return None


class SerializedDataHelper(object):

    def __init__(self, data, forms):
        self.forms = forms
        self.data = data
        self.zipped_data = []
        self._format_data()

    @property
    def cleaned_data(self):
        print('cleaned_data')
        print(self.zipped_data)
        return self.zipped_data

    def _format_data(self):
        for index, page_data in enumerate(self.data):
            self._cleaned_form_data(page_data, index)

    def _cleaned_form_data(self, page_data, index):
        self._zip_questions_and_answers(
            self._form_data_questions_only(page_data),
            self._form_questions_serialized(index),
        )

    def _form_data_questions_only(self, data):
        return {
            key: value
            for key, value in data.items()
            if key not in [
                'csrfmiddlewaretoken',
                'wizard_current_step',
                'wizard_goto_step',
                'form_pk',
            ]
        }

    def _form_questions_serialized(self, index):
        return self.forms[index].serialized

    def _zip_questions_and_answers(self, answers, questions):
        try:
            from pprint import pprint
            print('questions')
            pprint(questions)
            print('answers')
            pprint(answers)
            for answer_key, answer_value in answers.items():
                if answer_key not in [
                    'extra_info',
                    'extra_options',
                ]:
                    question = self._get_question(answer_key, questions)
                    self._parse_answer(answer_value, question)
        except Exception as e:
            # Questions that have changed since
            # the user last filled out the form
            # will likely raise an Exception
            logger.exception(e)

    def _get_question(self, answer_key, questions):
        related_question = None
        for question in questions:
            if answer_key == question['field_id']:
                related_question = question
        if related_question != None:
            return related_question
        else:
            raise ValueError('field_id={} not found in {}'.format(
                answer_key, questions))

    def _parse_answer(self, answer, question):
        from pprint import pprint
        print('question')
        pprint(question)
        print('answer')
        pprint(answer)
        if isinstance(answer, str):
            self._parse_text_answer(answer, question)
        else:
            pass

    def _parse_text_answer(self, answer, question):
        self.zipped_data.append({
            question['question_text']: [answer],
        })


class StorageHelper(object):
    data_manager = SerializedDataHelper

    def __init__(self, view):
        self.view = view

    @property
    def form_data(self):
        return {'data': [
            self.data_from_pk(form.pk)
            for form in self.view.manager.forms
        ]}

    @property
    def cleaned_form_data(self):
        return self.data_manager(
            self.form_data['data'],
            self.view.manager.forms,
        ).cleaned_data

    @property
    def post_form_pk(self):
        return self.view.form_pk(self.view.request.POST[
            self.view.form_pk_field])

    @property
    def post_data(self):
        data = self._data_from_key(self.post_form_pk)
        data.update(self.view.request.POST)
        return data

    def set_form_data(self):
        self.view.request.session[self.post_form_pk] = self.post_data

    def data_from_pk(self, pk):
        key = self.view.form_pk(pk)
        return self._data_from_key(key)

    def _data_from_key(self, key):
        return self.view.request.session.get(key, {})


class WizardView(views.edit.FormView):
    site_id = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'
    done_template_name = 'wizard_builder/review.html'
    form_pk_field = 'form_pk'
    steps_helper = StepsHelper
    storage_helper = StorageHelper
    form_manager = FormManager

    @property
    def steps(self):
        return self.steps_helper(self)

    @property
    def storage(self):
        return self.storage_helper(self)

    @property
    def manager(self):
        return self.form_manager(self)

    def form_pk(self, pk):
        return '{}_{}'.format(self.form_pk_field, pk)

    def get_form(self):
        return self.manager.forms[self.steps.current]

    def dispatch(self, request, step=None, *args, **kwargs):
        self.steps.set_from_get(step)
        if self.steps.finished(step):
            return self.dispatch_done(request, step, **kwargs)
        elif self.steps.overflowed(step):
            return self.render_last(**kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)

    def dispatch_done(self, request, step=None, *args, **kwargs):
        if self.steps.current_is_done:
            return self.render_finished(**kwargs)
        else:
            return self.render_done(**kwargs)

    def post(self, request, *args, **kwargs):
        self.steps.set_from_post()
        self.storage.set_form_data()
        return self.render_current()

    def get_context_data(self, **kwargs):
        if self.steps.current_is_done:
            self.template_name = self.done_template_name
            kwargs['form'] = None
            kwargs['form_data'] = self.storage.cleaned_form_data
            return super().get_context_data(**kwargs)
        else:
            return super().get_context_data(**kwargs)

    def render_done(self, **kwargs):
        return HttpResponseRedirect(self.steps.done_url)

    def render_finished(self, **kwargs):
        return self.render_to_response(self.get_context_data())

    def render_last(self, **kwargs):
        return HttpResponseRedirect(self.steps.last_url)

    def render_current(self, **kwargs):
        return HttpResponseRedirect(self.steps.current_url)
