import logging

from django.core.urlresolvers import reverse

logger = logging.getLogger(__name__)


def resolve_list(item):
    return item[0] if is_single_element_list(item) else item


def is_single_element_list(item):
    return bool(isinstance(item, list)) and (len(item) == 1)


def is_unselected_list(answer):
    return len(answer) == 0


def is_empty_text_box(answer):
    return len(answer) == 1 and not answer[0]


def get_by_pk(items, pk):
    for item in items:
        if str(item.get('pk')) == str(resolve_list(pk)):
            return item
    else:
        return {}


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
    def get_zipped_data(cls, data={}, forms={}):
        self = cls()
        self.data = data
        self.zipped_data = []
        self._parse_forms(forms)
        return self.zipped_data

    def _parse_forms(self, forms):
        for form in forms:
            self._parse_questions(form)

    def _parse_questions(self, form):
        for question in form:
            answer = self._get_question_answer(question)
            self._parse_answers(question, answer)

    def _parse_answers(self, question, answer):
        if question.get('type') == 'Singlelinetext':
            self._append_text_answer(answer, question)
        else:
            self._append_list_answers(answer, question)

    def _get_question_answer(self, question):
        return self.data.get(question.get('field_id'), '')

    def _append_text_answer(self, answer, question):
        self._append_answer(question, [answer])

    def _append_list_answers(self, answers, question):
        if not isinstance(answers, list):
            answers = [answers]
        choice_list = [
            self._get_choice_text(answer, question)
            for answer in answers
        ]
        self._append_answer(question, choice_list)

    def _append_answer(self, question, answer):
        if is_empty_text_box(answer) or is_unselected_list(answer):
            answer = [self.not_answered_text]
        self.zipped_data.append({
            question['question_text']: answer,
        })

    def _get_choice_text(self, answer, question):
        choice = self._get_choice(question, answer)
        choice_text = choice.get('text')
        return choice_text

    def _get_choice(self, question, answer):
        return get_by_pk(question.get('choices', []), answer)


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
    storage_data_key = 'wizard_form_data'
    storage_form_key = 'wizard_form_serialized'

    def __init__(self, view):
        # TODO: scope down inputs
        self.view = view
        self.init_storage()

    @property
    def form_data(self):
        return self.current_data_from_storage()

    @property
    def cleaned_form_data(self):
        storage = self.current_data_from_storage()
        return self.data_manager.get_zipped_data(
            data=storage[self.storage_data_key],
            forms=storage[self.storage_form_key],
        )

    @property
    def current_data(self):
        storage = self.current_data_from_storage()
        return storage[self.storage_data_key]

    @property
    def current_and_post_data(self):
        data = self.current_data
        data.update(self.view.current_step_data)
        return data

    def update(self):
        '''
        primary class functionality method, updates the data in storage
        '''
        data = self.current_and_post_data
        self.add_data_to_storage(data)

    def current_data_from_storage(self):
        # TODO: base class with NotImplementedError checks
        session = self.view.request.session
        return {
            self.storage_data_key: session.get(self.storage_data_key, {}),
            self.storage_form_key: session.get(self.storage_form_key, {}),
        }

    def add_data_to_storage(self, data):
        # TODO: base class with NotImplementedError checks
        session = self.view.request.session
        session[self.storage_data_key] = data

    def init_storage(self):
        # TODO: base class with NotImplementedError checks
        session = self.view.request.session
        session.setdefault(
            self.storage_form_key,
            self.view.get_serialized_forms(),
        )
        session.setdefault(
            self.storage_data_key,
            {},
        )


class WizardViewTemplateHelpers(object):
    # TODO: these sould all be context variables instead

    @property
    def wizard_prev_step_exists(self):
        return self.steps.current

    @property
    def wizard_next_is_done(self):
        return self.steps.next_is_done

    @property
    def wizard_current_step(self):
        return self.steps.current

    @property
    def wizard_goto_name(self):
        return self.steps.wizard_goto_name

    @property
    def wizard_current_name(self):
        return self.steps.wizard_current_name

    @property
    def wizard_review_name(self):
        return self.steps.review_name

    @property
    def wizard_next_name(self):
        return self.steps.next_name

    @property
    def wizard_back_name(self):
        return self.steps.back_name
