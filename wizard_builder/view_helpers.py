import logging

from django.core.urlresolvers import reverse

logger = logging.getLogger(__name__)


def resolve_list(item):
    if isinstance(item, list):
        return item[0]
    else:
        return item


def is_single_element_list(item):
    return bool(isinstance(item, list)) and (len(item) == 1)


def is_unselected_list(answer):
    return len(answer) == 0


def is_empty_text_box(answer):
    return len(answer) == 1 and not answer[0]


def get_by_pk(items, pk):
    for item in items:
        if str(item['pk']) == str(resolve_list(pk)):
            return item


class SerializedDataHelper(object):
    # TODO: move the zip functionality to PageForm or FormManager
    conditional_fields = [
        'extra_info',
        'extra_options',
    ]
    question_id_error_message = 'field_id={} not found in {}'
    choice_id_error_message = 'Choice(pk={}) not found in {}'
    choice_option_id_error_message = 'ChoiceOption(pk={}) not found in {}'
    not_answered_text = '[ Not Answered ]'

    @classmethod
    def get_zipped_data(cls, storage):
        self = cls()
        self.storage = storage
        self.zipped_data = []
        self._format_data()
        return self.zipped_data

    def _format_data(self):
        for index, page_data in enumerate(self.storage.form_data['data']):
            self._cleaned_form_data(page_data, index)

    def _cleaned_form_data(self, page_data, index):
        self._parse_all_questions(
            page_data,
            self._get_form_questions_serialized(index),
        )

    def _get_form_questions_serialized(self, index):
        return self.storage.view.forms[index].serialized

    def _parse_all_questions(self, answer_dict, questions):
        for question in questions:
            answer = self._get_question_answer(answer_dict, question)
            self._parse_answers(question, answer_dict, answer)

    def _parse_answers(self, question, answer_dict, answer):
        if question['type'] == 'Singlelinetext':
            self._append_text_answer(answer, question)
        else:
            answer_list = answer if isinstance(answer, list) else [answer]
            self._append_list_answers(answer_dict, answer_list, question)

    def _get_question_answer(self, answers, question):
        return answers.get(question['field_id'], '')

    def _append_text_answer(self, answer, question):
        self._append_answer(question, [answer])

    def _append_list_answers(self, answer_dict, answer_list, question):
        choice_list = [
            self._get_choice_text(answer_dict, answer, question)
            for answer in answer_list
            if answer
        ]
        self._append_answer(question, choice_list)

    def _append_answer(self, question, answer):
        if is_empty_text_box(answer) or is_unselected_list(answer):
            answer = [self.not_answered_text]
        self.zipped_data.append({
            question['question_text']: answer,
        })

    def _get_choice_text(self, answer_dict, answer, question):
        choice = self._get_choice(question, answer)
        choice_text = choice['text']
        if choice.get('extra_info_text') and answer_dict.get('extra_info'):
            choice_text += ': ' + resolve_list(answer_dict['extra_info'])
        if choice.get('options') and answer_dict.get('extra_options'):
            choice_text += ': ' + self._get_option_text(
                choice, answer_dict['extra_options'])
        return choice_text

    def _get_choice(self, question, answer):
        return get_by_pk(question['choices'], answer)

    def _get_option_text(self, choice, answer):
        return get_by_pk(choice['options'], answer)['text']


class StepsHelper(object):
    done_name = 'done'
    review_name = 'Review'
    next_name = 'Next'
    back_name = 'Back'
    wizard_goto_name = 'wizard_goto_step'
    wizard_current_name = 'wizard_current_step'
    wizard_form_fields = [
        wizard_current_name,
        wizard_goto_name,
    ]

    def __init__(self, view):
        self.view = view

    @property
    def step_count(self):
        return len(self.view.forms)

    @property
    def current(self):
        step = getattr(self.view, 'curent_step', 0)
        if isinstance(step, str):
            return step
        elif step <= self.last:
            return step
        else:
            return self.last

    @property
    def last(self):
        return self.step_count - 1

    @property
    def next(self):
        return self.adjust_step(1)

    @property
    def next_is_done(self):
        if isinstance(self.current, int):
            return self.next == self.done_name
        else:
            return False

    @property
    def current_is_done(self):
        return self.current == self.done_name

    @property
    def current_url(self):
        return self.url(self.current)

    @property
    def first_url(self):
        return self.url(0)

    @property
    def last_url(self):
        return self.url(self.last)

    @property
    def done_url(self):
        return self.url(self.done_name)

    @property
    def _goto_step_back(self):
        return self._goto_step(self.back_name)

    @property
    def _goto_step_next(self):
        return self._goto_step(self.next_name)

    @property
    def _goto_step_review(self):
        return self._goto_step(self.review_name)

    def parse_step(self, step):
        if step == self.done_name:
            return step
        else:
            return int(step)

    def url(self, step):
        return reverse(
            self.view.request.resolver_match.view_name,
            kwargs={'step': step},
        )

    def overflowed(self, step):
        return int(step) > int(self.last)

    def finished(self, step):
        return self._goto_step_review or step == self.done_name

    def set_from_post(self):
        if self._goto_step_back:
            self.view.curent_step = self.adjust_step(-1)
        if self._goto_step_next:
            self.view.curent_step = self.adjust_step(1)

    def adjust_step(self, adjustment):
        step = self.view.curent_step + adjustment
        if step >= self.step_count:
            return self.done_name
        else:
            return step

    def _goto_step(self, step_type):
        post = self.view.request.POST
        return post.get(self.wizard_goto_name, None) == step_type


class StorageHelper(object):
    data_manager = SerializedDataHelper

    def __init__(self, view):
        self.view = view

    @property
    def form_data(self):
        return {'data': [
            self.current_data_from_pk(form.pk)
            for form in self.view.forms
        ]}

    @property
    def cleaned_form_data(self):
        return self.data_manager.get_zipped_data(self)

    @property
    def current_and_post_data(self):
        current_data = self.current_data_from_key(self.view.wizard_current_step)
        current_data.update(self.view.current_step_data)
        return current_data

    def update(self):
        data = self.current_data_from_storage()
        data[self.view.wizard_current_step] = self.current_and_post_data
        self.add_data_to_storage(data)

    def current_data_from_pk(self, pk):
        key = self.form_pk(pk)
        return self.current_data_from_key(key)

    def current_data_from_key(self, form_key):
        data = self.current_data_from_storage()
        return data.get(form_key, {})

    def current_data_from_storage(self):
        return self.view.request.session.get('data', {})

    def add_data_to_storage(self, data):
        self.view.request.session['data'] = data
